package s3

import (
	"context"
	"fmt"
	"io"
	"log/slog"
	"mime"
	"os"
	"path/filepath"
	"time"

	conf "video_processing_worker/internal/config"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/feature/s3/transfermanager"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
)

type S3Service struct {
	config conf.Config
	Client *s3.Client
	logger *slog.Logger
}

func NewClient(settings conf.Config, logger *slog.Logger) (*S3Service, error) {
	cfg, err := config.LoadDefaultConfig(context.TODO(),
		config.WithRetryMaxAttempts(3),
		config.WithRegion(settings.S3.RegionName),
		config.WithCredentialsProvider(
			credentials.NewStaticCredentialsProvider(
				settings.S3.AwsAccessKeyId,
				settings.S3.AwsSecretAccessKey,
				"",
			),
		),
	)
	const op = "internal.s3.NewClient"
	if err != nil {
		return nil, fmt.Errorf("%s: %w", op, err)
	}
	client := s3.NewFromConfig(cfg, func(o *s3.Options) {
		if settings.S3.EndpointUrl != "" {
			o.BaseEndpoint = aws.String(settings.S3.EndpointUrl)
		}
		o.UsePathStyle = true
	})
	logger.Debug("Create client")

	return &S3Service{config: settings, Client: client, logger: logger}, nil

}

func (*S3Service) GetContentType(filename string) string {
	ext := filepath.Ext(filename)

	customTypes := map[string]string{
		".mpd": "application/dash+xml",
		".m4s": "video/iso.segment",
	}

	if ct, ok := customTypes[ext]; ok {
		return ct
	}

	if ct := mime.TypeByExtension(ext); ct != "" {
		return ct
	}

	return "application/octet-stream"
}

func (c *S3Service) GetKeyUpload(id string) string {
	return fmt.Sprintf("%s/%s", c.config.S3.KeyPrefixPrivateDraft, id)
}

func (c *S3Service) GetObject(bucketName string, key string) (*s3.GetObjectOutput, error) {
	result, err := c.Client.GetObject(context.TODO(), &s3.GetObjectInput{
		Bucket: aws.String(bucketName),
		Key:    aws.String(key),
	})
	const op = "internal.s3.S3Service.GetObject"
	if err != nil {
		return nil, fmt.Errorf("%s: %w", op, err)
	}
	return result, nil
}

func (c *S3Service) PutObject(bucketName string, key string, contentType string, file io.Reader) (*s3.PutObjectOutput, error) {
	output, err := c.Client.PutObject(
		context.TODO(),
		&s3.PutObjectInput{
			Bucket:      &bucketName,
			Key:         &key,
			Body:        file,
			ContentType: &contentType,
		},
	)
	const op = "internal.s3.S3Service.PutObject"
	if err != nil {
		return nil, fmt.Errorf("%s: %w", op, err)
	}
	return output, nil
}

func (c *S3Service) DeleteObjectsWithPrefix(bucketName string, prefix string) error {
	listObjectsInput := &s3.ListObjectsV2Input{
		Bucket: &bucketName,
		Prefix: &prefix,
	}
	paginator := s3.NewListObjectsV2Paginator(c.Client, listObjectsInput)

	const op = "internal.s3.S3Service.DeleteObjectsWithPrefix"
	for paginator.HasMorePages() {
		page, err := paginator.NextPage(context.TODO())
		if err != nil {
			return fmt.Errorf("%s: %w", op, err)
		}
		if len(page.Contents) == 0 {
			break
		}

		var objectsToDelete []types.ObjectIdentifier
		for _, obj := range page.Contents {
			objectsToDelete = append(objectsToDelete, types.ObjectIdentifier{
				Key: obj.Key,
			})
		}

		deleteInput := &s3.DeleteObjectsInput{
			Bucket: aws.String(bucketName),
			Delete: &types.Delete{
				Objects: objectsToDelete,
				Quiet:   aws.Bool(true),
			},
		}

		_, err = c.Client.DeleteObjects(context.TODO(), deleteInput)
		if err != nil {
			return fmt.Errorf("%s: %w", op, err)
		}
	}
	return nil
}

func (c *S3Service) DownloadFile(file *os.File, bucket string, key string) (int64, error) {
	uploader := transfermanager.New(c.Client)
	var size int64
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	output, err := uploader.DownloadObject(ctx, &transfermanager.DownloadObjectInput{
		Bucket:   aws.String(bucket),
		Key:      aws.String(key),
		WriterAt: file,
	})

	if err != nil {
		return 0, err
	}
	size = *output.ContentLength
	return size, nil
}
