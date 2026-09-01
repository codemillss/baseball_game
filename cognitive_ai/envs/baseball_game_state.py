class BaseballGameState:
    def __init__(self):
        self.inning = 1
        self.is_top = True
        self.outs = 0
        self.strikes = 0
        self.balls = 0
        self.score_away = 0
        self.score_home = 0
        self.bases = [False, False, False] # 1st, 2nd, 3rd

    def handle_pitch(self, outcome):
        if outcome == "STRIKE":
            self.strikes += 1
            if self.strikes == 3:
                self.outs += 1
                self.reset_count()
        elif outcome == "BALL":
            self.balls += 1
            if self.balls == 4:
                self.advance_runners()
                self.reset_count()
        
        if self.outs >= 3:
            self.change_inning()
            
    def handle_hit(self, outcome):
        self.reset_count()
        if outcome == "FOUL":
            if self.strikes < 2:
                self.strikes += 1
        elif outcome == "HOME RUN":
            runs = sum(self.bases) + 1
            self.add_runs(runs)
            self.bases = [False, False, False]
        elif outcome == "FAIR":
            # For simplicity, assume a single for now
            if self.bases[2]: self.add_runs(1)
            self.bases[2] = self.bases[1]
            self.bases[1] = self.bases[0]
            self.bases[0] = True
            
    def advance_runners(self):
        if self.bases[0]:
            if self.bases[1]:
                if self.bases[2]:
                    self.add_runs(1)
                self.bases[2] = True
            self.bases[1] = True
        self.bases[0] = True

    def reset_count(self):
        self.strikes = 0
        self.balls = 0
        
    def add_runs(self, runs):
        if self.is_top: self.score_away += runs
        else: self.score_home += runs
        
    def change_inning(self):
        self.outs = 0
        self.reset_count()
        self.bases = [False, False, False]
        if self.is_top:
            self.is_top = False
        else:
            self.is_top = True
            self.inning += 1

    def get_scoreboard(self):
        half = "Top" if self.is_top else "Bot"
        return f"{half} {self.inning} | AWAY {self.score_away} - {self.score_home} HOME | O:{self.outs} S:{self.strikes} B:{self.balls} | Bases: {int(self.bases[0])}{int(self.bases[1])}{int(self.bases[2])}"
