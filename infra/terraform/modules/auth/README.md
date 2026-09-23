# Auth module

Provisions **Amazon Cognito** for JWT-based authentication:

- A **user pool** with a strong password policy and (by default) admin-only user
  creation.
- An **app client** (no secret, PKCE `code` flow) whose id is the JWT audience
  the backend verifies.
- An optional **Hosted UI domain** for the login page.

The backend verifies RS256 tokens issued by this pool against its JWKS.

## Cost notes

Cognito is **free** up to 50,000 monthly active users — effectively **US$0** for
a dissertation demo.
