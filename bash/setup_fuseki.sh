set -o allexport; source docker/.env; set +o allexport

wget https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-4.2.0.tar.gz
tar xzf apache-jena-fuseki-4.2.0.tar.gz
mv apache-jena-fuseki-4.2.0 fuseki
rm apache-jena-fuseki-4.2.0.tar.gz
