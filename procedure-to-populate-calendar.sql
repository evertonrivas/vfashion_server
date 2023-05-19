DELIMITER //

create procedure populate(p_start DATE, p_end DATE)
begin
	declare v_date DATE;
	set v_date = p_start;
	while v_date <= p_end do
		insert into scm_calendar(calendar_date, year, quarter, month, week, day_of_week)
		VALUES (v_date, YEAR(v_date), QUARTER(v_date), MONTH(v_date), WEEK(v_date, 3), DAYOFWEEK(v_date));
		set v_date = date_add(v_date,interval 1 day);
	end while;
end //
DELIMITER ;