package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"video_processing_worker/internal/config"
	"video_processing_worker/internal/consumer"
	"video_processing_worker/internal/logger"
	"video_processing_worker/internal/s3"
	"video_processing_worker/internal/storage/postgresql"
	"video_processing_worker/internal/video"
)

func main() {
	config := config.MustLoad()
	logger := logger.ConfigLogger("DEV")
	client, err := s3.NewClient(*config, logger)
	if err != nil {
		logger.Error(err.Error())
		os.Exit(1)
	}
	repository, err := postgresql.NewRepository(config.StoragePath, logger)
	if err != nil {
		logger.Error(err.Error())
		os.Exit(1)
	}
	videoManager := video.NewVideoManager(*config, client, repository, logger)

	consumer, err := consumer.NewConsumer(config.Rabbitmq.Url, videoManager, logger)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	defer consumer.Close()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	ctx, stop := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)
	defer stop()
	consumer.ConsumeVideo(ctx)
}
