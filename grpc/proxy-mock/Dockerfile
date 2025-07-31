FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY main.go .
RUN go build -o proxy-mock main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/proxy-mock .

EXPOSE 50051
CMD ["./proxy-mock"]