set -o allexport; source bash/.env; set +o allexport

wget https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-4.3.1.tar.gzx
tar xzf apache-jena-fuseki-4.3.1.tar.gz
mv apache-jena-fuseki-4.3.1 fuseki
rm apache-jena-fuseki-4.3.1.tar.gz
