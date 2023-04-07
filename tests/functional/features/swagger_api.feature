Feature: AskAnna Swagger API
  As a developer,
  I want to find information about the askanna-api,
  So that i can develop integrations for askanna.

  Scenario: Swagger API Accessible
    Given AskAnna API-Homepage is available
    When the user goes to swagger-api
    Then the user sees the swagger-api
