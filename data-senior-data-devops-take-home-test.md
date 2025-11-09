# Senior Data DevOps Take-Home Test

## Concurrent Configuration Deployment Validator

### Scenario

Your organization manages microservices using YAML-based deployment configuration files. Each file defines how a service is deployed, for example:

```yaml
service: user-api
replicas: 3
image: myregistry.com/user-api:1.4.2
env:
  DATABASE_URL: postgres://db.internal:5432/users
  REDIS_URL: redis://cache.internal:6379
```

You need to build a **Python tool** that validates and monitors these configuration files efficiently, ensuring they adhere to organizational standards before deployment.

### Assignment Requirements

#### 1. File Discovery

- Recursively discover all `.yaml` or `.yml` files under a given directory.
- Handle large directory trees efficiently.

#### 2. Validation

- Ensure required keys exist: `service`, `image`, `replicas`.
- Validate:
  - `replicas` is an integer between 1 and 50.
  - `image` follows the pattern `<registry>/<service>:<version>`.
  - Environment variables are key–value pairs with uppercase keys.
- Collect detailed validation results for each file, including error messages.

#### 3. Concurrency

- Process files concurrently to handle large numbers of configurations efficiently.

#### 4. Reporting

- Produce a structured JSON report that summarizes:
  - Valid and invalid files with specific error reasons.
  - Count of services per registry.
  - Total number of issues found.
- Save the report to disk and print a summary to standard output.

#### 5. File Watching

- Implement a `--watch` mode that automatically revalidates files when they change.
- Output updated validation results when changes are detected.

#### 6. Plugin-Based Validation System

- Design the validator so that new validation rules can be added dynamically without modifying core logic.
- Each plugin should expose a standardized interface for contributing additional checks.

#### 7. Code Quality Requirements

- Modular structure with clear separation of concerns.
- Use type hints throughout.
- Use logging instead of print statements.
- Include robust exception handling for malformed files and I/O errors.
- Include at least two unit tests verifying validation and plugin functionality.
