# Phishing Detector Project

This project is designed to detect phishing attempts through various services that analyze emails, links, and provide verdicts based on the analysis. The architecture is microservices-based, allowing for scalability and maintainability.

## Project Structure

The project consists of the following components:

- **email-parser**: A service that parses emails and extracts relevant information.
- **phishing-detector**: A service that analyzes data to detect phishing attempts.
- **link-analyzer**: A service that analyzes URLs to determine their safety.
- **verdict-service**: A service that provides final verdicts based on analyses performed by other services.
- **gateway** (optional): A service that routes requests to the appropriate services.

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd phishing-detector-project
   ```

2. **Build and run the services**:
   You can use Docker Compose to build and run the services defined in the `docker-compose.yml` file. Run the following command:
   ```
   docker-compose up --build
   ```

3. **Access the services**:
   Each service will be accessible through the ports defined in the `docker-compose.yml` file. Refer to the file for specific port mappings.

## Usage

- The **email-parser** service can be used to parse incoming emails.
- The **phishing-detector** service analyzes data for potential phishing attempts.
- The **link-analyzer** service checks URLs for safety.
- The **verdict-service** aggregates results from the other services and provides a final verdict.
- The **gateway** service (if used) routes requests to the appropriate service based on the request type.

## Dependencies

Each service has its own `requirements.txt` file that lists the necessary Python packages. Make sure to install these dependencies for each service.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.