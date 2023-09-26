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

# Prepare the dest vars
source_file=".env_fief"
output_file=".env"
variables=("FIEF_CLIENT_ID" "FIEF_CLIENT_SECRET" "ENCRYPTION_KEY" "SECRET" "FIEF_MAIN_USER_EMAIL" "FIEF_MAIN_USER_PASSWORD" "FIEF_MAIN_ADMIN_API_KEY")

# Initialize an associative array to store the variable values
declare -A var_values

# Loop through the list of variables and extract their values
for var in "${variables[@]}"; do
    value=$(grep "\"$var=" "$source_file" | cut -d '=' -f 2-)
    value=$(echo $value | cut -d '"' -f 1)
    if [ -n "$value" ]; then
        var_values["$var"]="$value"
    fi
done

# Replace value of FIEF API key with generated key
fief_api_key=$(openssl rand -base64 32 | tr -d '+/=' | cut -c1-32)
var_values["FIEF_MAIN_ADMIN_API_KEY"]="$fief_api_key"

# Update .env file
for var in "${variables[@]}"; do
    sed -i.bak "s/^$var=.*/$var=$(echo $var_values["$var"])/" $output_file
done

# Remove tmp file
rm .env_fief
rm .env.bak