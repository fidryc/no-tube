package consumer

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"log/slog"
	"runtime"
	"video_processing_worker/internal/video"

	amqp "github.com/rabbitmq/amqp091-go"
)

type Consumer struct {
	connection   *amqp.Connection
	videoManager *video.VideoService
	logger       *slog.Logger
}

func NewConsumer(url string, videoManager *video.VideoService, logger *slog.Logger) (*Consumer, error) {
	connection, err := amqp.Dial(url)
	if err != nil {
		return nil, err
	}
	return &Consumer{connection: connection, videoManager: videoManager, logger: logger}, nil
}

const queueVideoName = "video_process"

func (consumer *Consumer) Close() error {
	err := consumer.connection.Close()
	const op = "internal.consumer.consumer.Close"
	if err != nil {
		return fmt.Errorf("%s: %w", op, err)
	}
	return nil
}

func (consumer *Consumer) ConsumeVideo(ctx context.Context) {
	ch, err := consumer.connection.Channel()
	if err != nil {
		log.Fatal(err)
	}
	defer ch.Close()
	msgs, err := ch.ConsumeWithContext(
		ctx,
		queueVideoName,
		"",
		false,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Panic(err)
	}
	MAXPROC := runtime.NumCPU() / 2
	pool := make(chan struct{}, MAXPROC)
	for d := range msgs {
		consumer.logger.Debug("Received a message")
		var msg MessageProcessVideo
		err := json.Unmarshal(d.Body, &msg)
		if err != nil {
			consumer.logger.Warn("Failed unmarshall msg", "err", err)
			d.Nack(false, true)
			continue
		}
		consumer.logger.Debug("Unmarshall msg", "msg", msg)
		consumer.videoManager.VideoProcessWithPool(ctx, d, pool, msg.VideoName, msg.Visibility)
	}
}
