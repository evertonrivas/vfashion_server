CREATE OR REPLACE FUNCTION populate(p_schema varchar,p_start DATE, p_end DATE)
RETURNS void AS $$
DECLARE
    v_date DATE := p_start;
BEGIN
	SET SEARCH_PATH TO p_schema;
    WHILE v_date <= p_end LOOP
		EXECUTE format(
		'INSERT INTO %I.scm_calendar(calendar_date,year,quarter,month,week,day_of_week) VALUES(%L,%L,%L,%L,%L,%L)',
		p_schema,
		v_date,
		EXTRACT(YEAR FROM v_date),
		EXTRACT(QUARTER FROM v_date),
		EXTRACT(MONTH FROM v_date),
		EXTRACT(WEEK FROM v_date),
		EXTRACT(DOW FROM v_date) + 1);

        v_date := v_date + INTERVAL '1 day';
    END LOOP;
END;
$$ LANGUAGE plpgsql;