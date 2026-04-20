package postgresql

import (
	"context"
	"database/sql"
	"fmt"
	"log/slog"
	"time"

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
	if err != nil {
		return nil, fmt.Errorf("%s: %w", op, err)
	}
	if err := db.Ping(); err != nil {
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
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_, err := r.stmtUpdateStatus.ExecContext(ctx, newStatus, id)

	const op = "storage.postgresql.CreateURL"
	if err != nil {
		return fmt.Errorf("%s: %w", op, err)
	}
	return nil
}
