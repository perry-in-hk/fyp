
def calculate_co2_emissions(distance, fuel_efficiency, total_elevation_gain, 
                           total_elevation_loss, payload_weight, max_payload,
                           co2_emission_factor, total_time):
    """
    Calculate CO2 emissions based on research findings from Posada-Henao et al.
    
    Parameters:
    -----------
    distance : float 
        Distance traveled in km
    fuel_efficiency : float
        Fuel efficiency in km/L (baseline efficiency on flat road)
    total_elevation_gain : float
        Total elevation gain in meters
    total_elevation_loss : float
        Total elevation loss in meters
    payload_weight : float
        Weight of payload in tonnes
    max_payload : float
        Maximum payload capacity in tonnes
    co2_emission_factor : float
        CO2 emission factor in g/L
    total_timw : float
        total travel time h
    
    Returns:
    --------
    float: CO2 emissions in kg
    """
    # Calculate average slope percentage
    avg_gain_slope_pct = (total_elevation_gain / (distance * 1000)) * 100
    avg_loss_slope_pct = (total_elevation_loss / (distance * 1000)) * 100
    
    # Calculate Speed Factor (VF) with "U-shaped" curve effect
    # Minimum consumption around 45 km/h for 3-axle or 35 km/h for 6-axle trucks
    optimal_speed = 50  # Average of optimal speeds base on reaerch
    total_time_hour = total_time / 3600
    speed_diff = abs(distance/total_time_hour - optimal_speed)
    vf = 1 + ((speed_diff / 50) ** 2) * 0.15  # Quadratic effect for U-shape
    
    # Calculate Load Factor (LF) with stronger impact
    lf = 1 + (payload_weight / max_payload) ** 1.2  # Slightly non-linear weight effect
    
    # Calculate slope effect with non-linear impact and threshold at 5%
    slope_effect = 1.0
    if avg_gain_slope_pct > 0:
        slope_factor = 0.2
        if avg_gain_slope_pct > 5:
            # Apply additional penalty for slopes over 5%
            slope_factor = 0.2 + 0.1 * (avg_gain_slope_pct - 5)
        
        # Weight-slope interaction effect
        weight_slope_interaction = 1 + (payload_weight / max_payload) * (avg_gain_slope_pct / 10)
        
        slope_effect += (avg_gain_slope_pct / 100) * slope_factor * weight_slope_interaction
    
    # Descent effect is smaller
    if avg_loss_slope_pct > 0:
        slope_effect -= (avg_loss_slope_pct / 100) * 0.05
    
    # Calculate CO2 emissions in kg
    co2_emissions = (distance / (fuel_efficiency * vf)) * slope_effect * lf * (co2_emission_factor / 1000)
    print(avg_gain_slope_pct)
    print(f"CO2 Emissions: {co2_emissions:.2f} kg")
    
    return co2_emissions

