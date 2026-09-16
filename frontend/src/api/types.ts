export interface Room {id:number;building:string;room_number:string;occupant_count:number;area_sqft:number|null}
export interface SummaryPoint {timestamp:string;kwh:number}
export interface TrendPoint extends SummaryPoint {rolling_7d:number|null;pct_change:number|null}
export interface RoomComparison {room:string;total_kwh:number;kwh_per_occupant:number}
export interface Anomaly extends SummaryPoint {is_anomaly:boolean;lower_bound:number;upper_bound:number}
export interface PeakPoint {day_of_week:string;[hour:string]:number|string}
export interface Bill {total_kwh:number;estimated_bill:number}
export interface Forecast {forecast:Record<string,number>;backtest_mape_percent:number|null;error?:string}
export interface AlertCheck {current_total:number;projected_month_total:number;limit:number|null;will_exceed:boolean}
