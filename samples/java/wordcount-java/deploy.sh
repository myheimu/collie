#~/bin/bash

mvn -U clean package
cd target
zip wordcount-java.zip wordcount-java-0.0.1-SNAPSHOT-xiaomi.jar library/*.jar 
