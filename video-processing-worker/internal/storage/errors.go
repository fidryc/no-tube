package storage

import "errors"

var (
	ErrUrlExists = errors.New("Url exists")
	ErrNoRows    = errors.New("No rows")
)
