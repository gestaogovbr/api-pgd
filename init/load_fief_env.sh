#!/bin/bash

# Copy the template file
cp init/.env.template .env

# Generate FIEF env vars
if [ $# -eq 0 ]; then
    # running in interactive terminal
    docker run -it ghcr.io/fief-dev/fief:latest fief quickstart --docker | tee -i .env_fief
else
    # running in a CI pipeline for creating a test environment
    docker run ghcr.io/fief-dev/fief:latest fief quickstart --docker "$@" | tee -i .env_fief
fi

# Generate admin API key
docker-compose run web python -c "import secrets; print(secrets.token_urlsafe())" > .fief_api_key

# Prepare the dest vars
source_file=".env_fief"
output_file=".env"
variables=("CLIENT_ID" "CLIENT_SECRET" "ENCRYPTION_KEY" "SECRET" "MAIN_USER_EMAIL" "MAIN_USER_PASSWORD" "MAIN_ADMIN_API_KEY")

# Initialize an associative array to store the variable values
declare -A var_values

# Loop through the list of variables and extract their values
for var in "${variables[@]}"; do
    value=$(grep "$var=" "$source_file" | cut -d '=' -f 2-)
    value=$(echo $value | cut -d '"' -f 1)
    if [ -n "$value" ]; then
        var_values["$var"]="$value"
    fi
done

# Replace value of FIEF API key with generated key
fief_api_key=$(cat .fief_api_key)
var_values["MAIN_ADMIN_API_KEY"]="$fief_api_key"

# Replace the extracted variable values
for var in "${variables[@]}"; do
    sed -i "s/FIEF_$var=.*/FIEF_$var=${var_values[$var]}/" $output_file
done

# Remove tmp file
rm .env_fief
rm .fief_api_key
