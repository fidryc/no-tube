package storage

type IRepository interface {
	UpdateStatus(id string, newStatus string) error
}
