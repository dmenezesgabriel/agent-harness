# Project Guidelines

## Stack

- Pnpm as package manager
- Vite as bundler
- Lit-Elements Web Components as components framework
- TypeScript as programming language
- Prettier for code formatting
- ESLint for linting
- Husky for Git hooks
- Commitlint for commit message linting
- Vitest for testing
- V8 for code coverage
- Storybook for UI component development
- MSW for mocking API requests
- StrikerJs for mutation testing
- Playwright for end-to-end testing

## Code Style

- Use camelCase for variable and function names
- Use PascalCase for component names
- Use kebab-case for file names
- Use single quotes for strings
- Use semicolons at the end of statements
- Use 2 spaces for indentation
- Use trailing commas in objects and arrays
- Use parentheses around arrow function parameters
- Use template literals for string concatenation
- Use descriptive variable and function names
- Avoid using `any` type in TypeScript
- Use interfaces for defining types in TypeScript
- Use React hooks for state management and side effects
- Use functional components instead of class components
- Use PropTypes for type checking in React components
- Use JSDoc comments for documenting functions and components
- Use Storybook for developing and testing UI components in isolation
- Use MSW for mocking API requests in tests
- Use Next.js for Static Site Generation (SSG) to improve performance and SEO
- Follow the principles of DRY (Don't Repeat Yourself) and KISS (Keep It Simple, Stupid)

## Testing

- Write unit tests for all components and functions
- Write integration tests for critical user flows
- Write end-to-end tests for the entire application
- Aim for high test coverage, but prioritize meaningful tests over achieving 100% coverage
- Use descriptive test names that clearly indicate what is being tested
- Use Arrange-Act-Assert (AAA) pattern for structuring tests
- Mock external dependencies and API calls in tests to ensure isolation
- Use code coverage tools to identify untested code and improve test coverage
- Cover edge cases and error handling in tests
