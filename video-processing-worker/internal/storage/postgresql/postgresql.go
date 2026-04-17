package postgresql

import (
	"database/sql"
	"fmt"
	"log/slog"

	_ "github.com/lib/pq"
)

type Repository struct {
	Db               *sql.DB
	logger           *slog.Logger
	stmtUpdateStatus *sql.Stmt
}

func NewRepository(url string, logger *slog.Logger) (*Repository, error) {
	db, err := sql.Open("postgres", url)

	const op = "storage.postgresql.NewRepository"
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("%s: %w", op, err)
	}
	if err != nil {
		return nil, fmt.Errorf("%s: %w", op, err)
	}
	logger.Info("Successful connection to the database")

	stmtUpdateStatus, err := db.Prepare(
		`
		UPDATE videos
		SET processing_status = $1
		WHERE id = $2
		`,
	)
	if err != nil {
		return nil, fmt.Errorf("%s: %w", op, err)
	}

	return &Repository{Db: db, logger: logger, stmtUpdateStatus: stmtUpdateStatus}, nil
}

func (r *Repository) UpdateStatus(id string, newStatus string) error {
	_, err := r.stmtUpdateStatus.Exec(newStatus, id)

	const op = "storage.postgresql.CreateURL"
	if err != nil {
		return fmt.Errorf("%s: %w", op, err)
	}
	return nil
}
