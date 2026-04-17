package config

import (
	"log"
	"os"

	"gopkg.in/yaml.v3"
)

type S3Config struct {
	AwsAccessKeyId             string `yaml:"aws_access_key_id"`
	AwsSecretAccessKey         string `yaml:"aws_secret_access_key"`
	EndpointUrl                string `yaml:"endpoint_url"`
	RegionName                 string `yaml:"region_name"`
	KeyPrefixPrivateDraft      string `yaml:"key_prefix_private_draft"`
	KeyPrefixPrivateProcessing string `yaml:"key_prefix_private_processing"`
	BucketPrivate              string `yaml:"bucket_private"`
	KeyPrefixPublic            string `yaml:"key_prefix_public"`
}

type RabbitmqConfig struct {
	Url string `yaml:"url"`
}

type Config struct {
	Env         string         `yaml:"env"`
	StoragePath string         `yaml:"storage_path"`
	S3          S3Config       `yaml:"s3"`
	Rabbitmq    RabbitmqConfig `yaml:"rabbitmq"`
}

func MustLoad() *Config {
	config_path := os.Getenv("CONFIG_PATH")

	if config_path == "" {
		log.Fatalf("CONFIG_PATH is not set")
	}

	bytes, err := os.ReadFile(config_path)
	if err != nil {
		log.Fatalf("cannot read config: %s", err)
	}
	var config Config
	yaml.Unmarshal(bytes, &config)
	return &config
}
