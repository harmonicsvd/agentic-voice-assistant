export const CalendarBackground = () => {
  const today = new Date().getDate();
  const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
  
  const cells = Array.from({ length: 35 }, (_, i) => {
    const day = ((i - 1) % 31) + 1;
    return { day, isToday: day === today };
  });

  return (
    <div className="cal-bg">
      <div className="cal-header-row">
        {days.map((day) => (
          <div key={day} className="cal-day-label">{day}</div>
        ))}
      </div>
      <div className="cal-cells">
        {cells.map((cell, i) => (
          <div key={i} className="cal-cell">
            <div className={`cal-num ${cell.isToday ? 'today' : ''}`}>{cell.day}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
