# Type Patterns by Language

Use the idiomatic pattern for the project's language. Detect the language from `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, or `build.gradle`.

## TypeScript

### Port interface

```typescript
export interface UserRepository {
  findById(id: UserId): Promise<User | null>;
  findByEmail(email: Email): Promise<User | null>;
  save(user: User): Promise<void>;
}
```

### Request/response types

```typescript
export type CreateUserRequest = {
  readonly email: string;
  readonly name: string;
};

export type CreateUserResponse = {
  readonly id: UserId;
  readonly createdAt: string; // ISO-8601 UTC
};
```

### Domain event

```typescript
export type UserCreatedEvent = {
  readonly type: "user.created";
  readonly userId: UserId;
  readonly email: Email;
  readonly occurredAt: string; // ISO-8601 UTC
};
```

### Value object (branded type)

```typescript
export type UserId = string & { readonly __brand: "UserId" };
export type Email = string & { readonly __brand: "Email" };
```

Branded types prevent accidental field swaps at compile time.

---

## Python

### Port (Protocol — preferred over ABC)

```python
from typing import Protocol

class UserRepository(Protocol):
    def find_by_id(self, user_id: UserId) -> User | None: ...
    def find_by_email(self, email: Email) -> User | None: ...
    def save(self, user: User) -> None: ...
```

Use `Protocol` from `typing` (Python 3.8+). Prefer `Protocol` over `ABC` for ports — it allows structural subtyping without requiring explicit inheritance in adapters.

### Request/response types (frozen dataclass)

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class CreateUserRequest:
    email: str
    name: str

@dataclass(frozen=True)
class CreateUserResponse:
    id: UserId
    created_at: datetime
```

Use `frozen=True` for immutable DTOs.

### Domain event

```python
@dataclass(frozen=True)
class UserCreatedEvent:
    user_id: UserId
    email: Email
    occurred_at: datetime  # UTC
```

### Value object (NewType)

```python
from typing import NewType

UserId = NewType("UserId", str)
Email = NewType("Email", str)
```

---

## Go

### Port interface

```go
type UserRepository interface {
    FindByID(ctx context.Context, id UserID) (*User, error)
    FindByEmail(ctx context.Context, email Email) (*User, error)
    Save(ctx context.Context, user *User) error
}
```

Always include `context.Context` as the first parameter for I/O operations.

### Request/response types

```go
type CreateUserRequest struct {
    Email string `json:"email"`
    Name  string `json:"name"`
}

type CreateUserResponse struct {
    ID        UserID    `json:"id"`
    CreatedAt time.Time `json:"created_at"`
}
```

### Domain event

```go
type UserCreatedEvent struct {
    UserID     UserID    `json:"user_id"`
    Email      Email     `json:"email"`
    OccurredAt time.Time `json:"occurred_at"` // UTC
}
```

### Value object (named type)

```go
type UserID string
type Email string
```

---

## Rust

### Port (trait)

```rust
pub trait UserRepository {
    fn find_by_id(&self, id: &UserId) -> Option<User>;
    fn find_by_email(&self, email: &Email) -> Option<User>;
    fn save(&self, user: &User) -> Result<(), RepositoryError>;
}
```

### Domain event

```rust
#[derive(Debug, Clone)]
pub struct UserCreatedEvent {
    pub user_id: UserId,
    pub email: Email,
    pub occurred_at: DateTime<Utc>,
}
```

---

## Java / Kotlin

### Port interface (Java)

```java
public interface UserRepository {
    Optional<User> findById(UserId id);
    Optional<User> findByEmail(Email email);
    void save(User user);
}
```

### Port interface (Kotlin)

```kotlin
interface UserRepository {
    fun findById(id: UserId): User?
    fun findByEmail(email: Email): User?
    fun save(user: User)
}
```

---

## OpenAPI (cross-service API contracts)

```yaml
paths:
  /users:
    post:
      summary: Create a user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CreateUserRequest"
      responses:
        "201":
          description: User created
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/CreateUserResponse"
        "422":
          description: Validation error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ValidationError"

components:
  schemas:
    CreateUserRequest:
      type: object
      required: [email, name]
      properties:
        email:
          type: string
          format: email
        name:
          type: string
          maxLength: 100
    CreateUserResponse:
      type: object
      required: [id, created_at]
      properties:
        id:
          type: string
          format: uuid
        created_at:
          type: string
          format: date-time
    ValidationError:
      type: object
      required: [code, message, field]
      properties:
        code:
          type: string
        message:
          type: string
        field:
          type: string
```
