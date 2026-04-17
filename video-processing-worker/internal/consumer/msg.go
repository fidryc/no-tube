package consumer

type MessageProcessVideo struct {
	VideoName  string `json:"video_name"`
	Visibility string `json:"visibility,omitempty"`
}
