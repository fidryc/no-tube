FROM golang:1.25-alpine AS builder

WORKDIR /build

COPY go.mod go.sum ./

RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -o /worker ./cmd/worker


FROM alpine:3.22

WORKDIR /app

RUN apk add --no-cache ca-certificates ffmpeg

COPY --from=builder /worker /app/worker

CMD ["/app/worker"]