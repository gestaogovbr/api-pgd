#!/bin/bash

# Copy the template file
cp init/.env.template .env

# Generate FIEF env vars
docker run -it ghcr.io/fief-dev/fief:latest fief quickstart --docker | tee -i .env_fief

# Prepare the dest vars
source_file=".env_fief"
template_file=".env"
variables=("CLIENT_ID" "CLIENT_SECRET" "ENCRYPTION_KEY" "SECRET" "MAIN_USER_EMAIL" "MAIN_USER_PASSWORD")

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

# Replace the extracted variable values
for var in "${variables[@]}"; do
    sed -i "s/FIEF_$var=.*/FIEF_$var=${var_values[$var]}/" $template_file
done

# Remove tmp file
rm .env_fief