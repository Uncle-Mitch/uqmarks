finch cp courses.sql uqmarks-db-1:/tmp/courses.sql
finch exec -it uqmarks-db-1 sh
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/courses.sql
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/search_logs.sql
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/20260225_add_event_type_to_search_logs.sql

finch cp search_logs.csv uqmarks-db-1:/tmp/search_logs.csv

docker exec -it uqmarks-db-1 sh
docker cp courses.sql uqmarks-db-1:/tmp/courses.sql
docker cp search_logs.csv uqmarks-db-1:/tmp/search_logs.csv

docker cp course_new3.sql uqmarks-db-1:/tmp/course_new3.sql

psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/course_new2.sql
