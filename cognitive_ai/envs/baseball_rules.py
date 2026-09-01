import numpy as np

class BaseballUmpire:
    def __init__(self):
        # Strike Zone limits based on h1_baseball_match.xml
        self.sz_x_min = -0.215
        self.sz_x_max = 0.215
        self.sz_y_min = -0.215
        self.sz_y_max = 0.215
        self.sz_z_min = 0.5
        self.sz_z_max = 1.1

    def is_in_strike_zone(self, ball_pos):
        """ Check if a single point is inside the strike zone box """
        x, y, z = ball_pos
        return (self.sz_x_min <= x <= self.sz_x_max and 
                self.sz_y_min <= y <= self.sz_y_max and 
                self.sz_z_min <= z <= self.sz_z_max)

    def check_pitch_outcome(self, ball_trajectory):
        """
        Given a list of ball positions (x, y, z) over time,
        determine if it passed through the strike zone.
        """
        for pos in ball_trajectory:
            if self.is_in_strike_zone(pos):
                return "STRIKE"
        return "BALL"

    def check_hit_outcome(self, land_pos):
        """
        Given the (x, y, z) position where the ball landed,
        determine FOUL, FAIR, or HOME RUN.
        Assuming foul lines are at y = |x|.
        """
        x, y, z = land_pos
        
        # If it lands behind home plate
        if y < 0:
            return "FOUL"
            
        # Distance from home
        dist = np.sqrt(x**2 + y**2)
        
        # Check Foul lines (y = |x|)
        # The angle from home plate. center field is x=0, y>0 (angle 90).
        # 1st base is x>0, y=x (angle 45).
        # 3rd base is x<0, y=-x (angle 135).
        # FAIR territory is between 45 and 135 degrees.
        # This is exactly y >= |x|.
        
        is_fair = y >= abs(x)
        
        if is_fair:
            if dist > 120.0: # 120 meters for a home run
                return "HOME RUN"
            return "FAIR"
        else:
            return "FOUL"
