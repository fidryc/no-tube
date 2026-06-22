package main

import (
	"context"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"strings"
	"time"
	"video_processing_worker/internal/config"
	"video_processing_worker/internal/logger"
	s3_service "video_processing_worker/internal/s3"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

var httpClient = &http.Client{Timeout: 30 * time.Second}

type VideoProxyAPI struct {
	s3Service *s3_service.S3Service
	config    *config.Config
	logger    *slog.Logger
}

// GET /segment/{videoID}/{fileName}
func (v *VideoProxyAPI) segmentHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		w.WriteHeader(http.StatusMethodNotAllowed)
	}

	parts := strings.Split(r.URL.Path, "/")

	v.logger.Info("parts", "parts", parts)
	if len(parts) != 4 {
		http.NotFound(w, r)
		return
	}

	videoID := string(parts[2])
	fileName := string(parts[3])
	result, err := v.s3Service.Client.GetObject(context.TODO(), &s3.GetObjectInput{
		Bucket: aws.String(v.config.S3.BucketPrivate),
		Key:    aws.String(v.s3Service.GetKeyFileProcessingPrivate(videoID, fileName)),
	})
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
	}
	defer result.Body.Close()

	_, err = io.Copy(w, result.Body)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
	}
	w.WriteHeader(http.StatusOK)
	v.logger.Debug("Succesufely processing the segment")
}

func CORSMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "*")
		w.Header().Set("Access-Control-Allow-Headers ", "*")
		next.ServeHTTP(w, r)
	})
}

func main() {
	config := config.MustLoad()
	logger := logger.ConfigLogger("DEV")

	s3Service, err := s3_service.NewClient(*config, logger)
	if err != nil {
		logger.Error("Fail start", "error", err)
		os.Exit(1)
	}
	VideoProxyAPI := VideoProxyAPI{s3Service: s3Service, config: config, logger: logger}
	mux := http.NewServeMux()
	mux.HandleFunc("/segment/", VideoProxyAPI.segmentHandler)

	fmt.Println("Proxy listening on :8001")
	http.ListenAndServe(":8001", CORSMiddleware(mux))
}
