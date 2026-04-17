package ffmpeg

import (
	"fmt"
	"os"
	"os/exec"
)

func GeneratePath(id string) string {
	return "./tmp/video-processing/" + id
}
func createDir(path string) error {
	const op = "internal.ffmpeg.createDir"
	if _, err := os.Stat(path); err == nil {
		return fmt.Errorf("%s: %s", op, path)
	}
	os.Mkdir(path, 0700)
	return nil
}

func ProcessingVideo(inputPath string, path string) error {
	const op = "internal.ffmpeg.ProcessingVideo"
	if err := createDir(path); err != nil {
		return fmt.Errorf("%s: %w", op, err)
	}
	err := CreateDash(inputPath, fmt.Sprintf("%s/%s.mpd", path, "dash"))
	if err != nil {
		return fmt.Errorf("%s: %w", op, err)
	}
	return nil
}

func CreateDash(inputPath string, outputPath string) error {
	cmd := exec.Command(
		"ffmpeg",
		"-i", inputPath,

		"-map", "0:v",
		"-map", "0:v",
		"-map", "0:a?",
		"-map", "0:a?",

		"-c:v", "libx264",
		"-pix_fmt", "yuv420p",

		"-b:v:0", "2000k",
		"-s:v:0", "1280x720",
		"-profile:v:0", "main",

		"-b:v:1", "800k",
		"-s:v:1", "640x360",
		"-profile:v:1", "baseline",

		"-c:a", "aac",
		"-b:a", "128k",
		"-ar", "48000",

		"-g", "48",
		"-keyint_min", "48",
		"-sc_threshold", "0",

		"-use_timeline", "1",
		"-use_template", "1",

		"-f", "dash",

		outputPath,
	)

	const op = "internal.ffmpeg.CreateDash"
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("%s: %w", op, fmt.Errorf("%s: %w", out, err))
	}

	return nil
}

func ConvertToQualityVideo(outputDir string, quality string, inputPath string) error {
	outputPath := fmt.Sprintf("%s/%s.mp4", outputDir, quality)

	cmd := exec.Command(
		"ffmpeg",
		"-i", inputPath,

		"-c:v", "libx264",
		"-b:v", "1000k",
		"-s", quality,

		"-c:a", "aac",
		"-b:a", "128k",

		outputPath,
	)

	const op = "internal.ffmpeg.ConvertToQualityVideo"
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("%s: %w", op, fmt.Errorf("%s: %w", out, err))
	}

	return nil
}
