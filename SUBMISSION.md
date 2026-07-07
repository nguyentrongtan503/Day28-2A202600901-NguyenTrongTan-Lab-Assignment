# BÁO CÁO NỘP BÀI - LAB #28: FULL PLATFORM INTEGRATION SPRINT

## 1. Thông tin học viên
- **Họ và tên**: NGUYỄN TRỌNG TẤN
- **Mã học viên**: 2A202600901
- **Đường dẫn repository**: https://github.com/nguyentrongtan503/Day28-2A202600901-NguyenTrongTan-Lab-Assignment.git

---

## 2. Kết Quả Smoke Tests & Production Readiness

### 2.1 Kết Quả Smoke Tests (8/8 Passed)
Tất cả 8 test cases kiểm tra tích hợp đầu-cuối đều đã vượt qua thành công:
```text
smoke-tests/test_e2e.py::TestHappyPath::test_full_inference_returns_200 PASSED [ 12%]
smoke-tests/test_e2e.py::TestHappyPath::test_health_check_passes PASSED  [ 25%]
smoke-tests/test_e2e.py::TestDataIngestion::test_kafka_ingest_and_qdrant_store PASSED [ 37%]
smoke-tests/test_e2e.py::TestObservability::test_prometheus_scrapes_api_gateway PASSED [ 50%]
smoke-tests/test_e2e.py::TestObservability::test_grafana_dashboard_accessible PASSED [ 62%]
smoke-tests/test_e2e.py::TestFailurePath::test_invalid_request_returns_422 PASSED [ 75%]
smoke-tests/test_e2e.py::TestFailurePath::test_timeout_handled_gracefully PASSED [ 87%]
smoke-tests/test_e2e.py::TestFeatureStore::test_feast_redis_has_features PASSED [100%]

============================= 8 passed in 11.31s ==============================
```

### 2.2 Production Readiness Score (100%)
```text
=== RELIABILITY ===
  [PASS] Health check endpoint
  [PASS] API Gateway responds

=== OBSERVABILITY ===
  [PASS] Prometheus up
  [PASS] Grafana up
  [PASS] Metrics endpoint exposed

=== SECURITY ===
  [PASS] Unauthorized request rejected

=== VECTOR STORE ===
  [PASS] Qdrant healthy
  [PASS] Collection exists

=== FEATURE STORE ===
  [PASS] Redis reachable

=== KAFKA ===
  [PASS] Kafka topics exist

========================================
Production Readiness Score: 10/10 = 100%
Target: >80% 🏆 Status: READY
```

---

## 3. Câu Hỏi Trả Lời Khi Nộp (5 Submission Questions)

### Câu 1: Phân tích các trade-offs trong thiết kế kiến trúc AI platform của bạn. Bạn đã cân bằng giữa performance, reliability, và maintainability như thế nào?
- **Performance**: Để tối ưu hiệu năng cho API Gateway khi xử lý các request real-time, toàn bộ luồng lưu trữ lịch sử, tiền xử lý và đồng bộ RAG được đẩy xuống xử lý bất đồng bộ thông qua Kafka và Pipeline Worker. Điều này giúp API Gateway giải phóng tài nguyên I/O đĩa và chỉ tập trung vào việc giao tiếp với LLM/Embedding serving.
- **Reliability**: Hệ thống được phân tách thành các microservices độc lập thông qua Docker Compose. Nếu một service lưu trữ (như Qdrant hay Redis) tạm thời bị crash, luồng ghi nhận event chính qua Kafka vẫn hoạt động bình thường, các tin nhắn được lưu đệm an toàn trong hàng đợi của Kafka mà không bị mất dữ liệu.
- **Maintainability**: Kiến trúc tách biệt rõ ràng giữa luồng đồng bộ dữ liệu (data sync pipeline) và luồng suy luận trực tiếp (inference path) giúp dễ dàng mở rộng và bảo trì. Mỗi dịch vụ có thể được cập nhật độc lập mà không ảnh hưởng đến các thành phần khác.

### Câu 2: Trong kiến trúc hybrid (Local + Kaggle), bạn xử lý ngắt kết nối giữa local và Kaggle như thế nào? Có cơ chế fallback không?
- **Cơ chế Timeout**: Các lời gọi HTTP API từ local đến vLLM và embedding services chạy trên Kaggle được bọc trong các block `try-except` với tham số `timeout` nghiêm ngặt (như 10s đối với embedding).
- **Cơ chế Fallback**: 
  - Nếu kết nối bị mất hoặc phản hồi chậm, API Gateway sẽ bắt lỗi ngoại lệ `Timeout` và xử lý graceful (trả về lỗi thân thiện cho client thay vì làm sập ứng dụng).
  - Pipeline Worker cũng bắt lỗi kết nối để ghi nhận log và duy trì vòng lặp lắng nghe Kafka, đảm bảo dữ liệu sự kiện vẫn được giữ lại và tiếp tục đồng bộ khi kết nối Kaggle được khôi phục.

### Câu 3: Giải thích cách event-driven architecture với Kafka giúp decouple các components trong AI platform của bạn.
- **Decoupling Producer & Consumer**: API Gateway (Producer) chỉ làm nhiệm vụ đẩy dữ liệu sự kiện thô vào Kafka topic `data.raw` rồi phản hồi ngay lập tức cho client. Nó hoàn toàn không cần biết dữ liệu đó sẽ được lưu ở đâu, xử lý ra sao, và bởi những dịch vụ nào.
- **Nhà tiêu thụ độc lập**: Pipeline Worker (Consumer) lắng nghe dữ liệu từ Kafka bất cứ khi nào nó sẵn sàng và tự điều phối tốc độ xử lý của mình (backpressure handling). Nếu worker bị khởi động lại hoặc tạm ngưng, dữ liệu trong Kafka vẫn được lưu trữ tạm thời và sẽ được tiêu thụ tiếp khi worker online trở lại.

### Câu 4: Bạn đã implement observability như thế nào? Logs, metrics, và traces được thu thập và visualized ra sao?
- **Logs**: Toàn bộ logs từ các containers chạy trên Docker Compose được Docker daemon gom lại tập trung, có thể truy vấn qua lệnh `docker compose logs`.
- **Metrics**: API Gateway tích hợp sẵn `prometheus-fastapi-instrumentator` để tự động expose các chỉ số hiệu năng (throughput, latency, status codes) tại endpoint `/metrics`. Prometheus sẽ định kỳ scrape dữ liệu này để lưu trữ dạng timeseries.
- **Visualization**: Grafana kết nối trực tiếp với Prometheus nguồn dữ liệu để trực quan hóa hiệu năng hệ thống lên Dashboard tại cổng 3000.
- **Traces**: LangSmith được tích hợp vào API Gateway thông qua biến môi trường để trace vết luồng đi chi tiết của các prompts và kết quả phản hồi của LLM.

### Câu 5: Nếu một service trong stack (ví dụ: Qdrant hoặc Kafka) bị crash, hệ thống của bạn sẽ xử lý như thế nào? Có graceful degradation không?
- **Qdrant hoặc Redis (Feast) bị crash**: Pipeline worker sẽ bắt ngoại lệ và bỏ qua bước ghi vector/feature tương ứng, chỉ tiếp tục ghi nhận log lỗi và lưu dữ liệu thô vào Delta Lake Parquet để tránh làm ngắt quãng toàn bộ tiến trình.
- **Kafka bị crash**: API Gateway vẫn hoạt động bình thường đối với luồng chat trực tiếp, chỉ tạm ngưng việc đẩy lịch sử cuộc gọi vào Kafka. Người dùng vẫn nhận được câu trả lời từ chatbot.
- **Tự động khôi phục**: Các chính sách khởi động lại (`restart: always` hoặc `restart: unless-stopped`) được định nghĩa trong `docker-compose.yml` đảm bảo các container bị sập sẽ tự động restart để khôi phục dịch vụ.
