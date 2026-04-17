package video

import (
	"errors"
	"fmt"
	"io/fs"
	"log/slog"
	"os"
	"path/filepath"
	"video_processing_worker/internal/config"
	"video_processing_worker/internal/ffmpeg"
	"video_processing_worker/internal/s3"
	"video_processing_worker/internal/storage/postgresql"

	"github.com/rabbitmq/amqp091-go"
)

type VideoService struct {
	config     config.Config
	s3_service *s3.S3Service
	repository *postgresql.Repository
	logger     *slog.Logger
}

func NewVideoManager(config config.Config, s3_service *s3.S3Service, repository *postgresql.Repository, logger *slog.Logger) *VideoService {
	return &VideoService{s3_service: s3_service, repository: repository, config: config, logger: logger}
}

func (v *VideoService) GenerateDraftPath(fileName string) string {
	return fmt.Sprintf("./tmp/%s/%s", v.config.S3.KeyPrefixPrivateDraft, fileName)
}

// Путь к папке в которую сохранится dash
func (*VideoService) GenerateProcessingPath(fileName string) string {
	return fmt.Sprintf("./tmp/video-processing/%s", fileName)
}

func (v *VideoService) cleanFile(path string, file *os.File) {
	file.Close()
	err := os.Remove(path)
	if err != nil {
		v.logger.Warn("Failed remove file", "path", path)
	}
}

func (v *VideoService) VideoProcess(id string, statusVisibility string) error {
	const op = "internal.video.VideoService.VideoProcess"
	err := v.repository.UpdateStatus(id, PROCESSING)
	if err != nil {
		v.logger.Warn("Failed update status", "id", id, "status", statusVisibility)
		return fmt.Errorf("%s: %w", op, err)
	}

	key_s3_private_draft := v.s3_service.GetKeyUpload(id)
	// Скачиваем файл из s3 себе локально

	pathFile := v.GenerateDraftPath(id)
	file, err := os.Create(pathFile)
	if err != nil {
		v.logger.Warn("Failed create file", "path_file", pathFile)
		return fmt.Errorf("%s: %w", op, err)
	}
	defer v.cleanFile(pathFile, file)

	_, err = v.s3_service.DownloadFile(file, v.config.S3.BucketPrivate, key_s3_private_draft)
	if err != nil {
		v.logger.Warn("Failed DownloadFile file", "pathFile", pathFile)
		return fmt.Errorf("%s: %w", op, err)
	}

	pathOutputLocal := v.GenerateProcessingPath(id) // Директория в которую сохраняется dash
	// Создаем dash через ffpmeg
	err = ffmpeg.ProcessingVideo(pathFile, pathOutputLocal)
	if err != nil {
		v.logger.Warn("Failed convert file to dash", "pathFile", pathFile, "pathOutputLocal", pathOutputLocal)
		return fmt.Errorf("%s: %w", op, err)
	}

	// проходим по всем файлам папки c dash и кидаем в s3
	errWalk := filepath.Walk(pathOutputLocal, func(path string, info fs.FileInfo, err error) error {
		// При какой то ошибке нужно задеферить очистку s3 и очистку локального
		if err != nil {
			// Возможно стоит добавить лог при ошибке очистки s3
			return err
		}
		if info.IsDir() {
			return nil
		}
		file, err := os.Open(path)
		if err != nil {
			return err
		}
		defer file.Close()
		_, err = v.s3_service.PutObject(
			v.config.S3.BucketPrivate,
			fmt.Sprintf("%s/%s/%s", v.config.S3.KeyPrefixPrivateProcessing, id, info.Name()),
			v.s3_service.GetContentType(info.Name()),
			file,
		)
		if err != nil {
			return err
		}
		return nil
	})
	// Удалем у себя dash
	err = os.RemoveAll(pathOutputLocal)
	if err != nil {
		v.logger.Warn("Failed clean dir", "pathOutputLocal", pathOutputLocal)
		return fmt.Errorf("%s: %w", op, err)
	}
	if errWalk != nil {
		// Если была ошибка при загрузке файла, то очищаю s3
		err := v.s3_service.DeleteObjectsWithPrefix(v.config.S3.BucketPrivate, fmt.Sprintf("%s/%s", v.config.S3.KeyPrefixPrivateProcessing, id))
		if err != nil {
			v.logger.Warn("Failed clean a dash fragments in s3")
			combineErr := errors.Join(err, errWalk)
			return fmt.Errorf("%s: %w", op, combineErr)
		}
		return fmt.Errorf("%s: %w", op, errWalk)
	}
	// TODO: Изменить статус на загружено

	return nil
}

func (v *VideoService) VideoProcessWithPool(d amqp091.Delivery, pool chan struct{}, id string, statusVisibility string) {
	pool <- struct{}{}
	go func() {
		err := v.VideoProcess(id, statusVisibility)
		if err != nil {
			v.repository.UpdateStatus(id, FAILED)
			v.logger.Debug("Failed process video")
			d.Nack(false, true)
		} else {
			v.repository.UpdateStatus(id, READY)
			v.logger.Debug("Successfully processed")
			d.Ack(false)
		}

		<-pool
	}()
}
