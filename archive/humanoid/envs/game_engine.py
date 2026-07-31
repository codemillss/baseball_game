import numpy as np
from typing import Dict, Any, Tuple

class BaseballGameEngine:
    def __init__(self, max_innings: int = 9):
        self.max_innings = max_innings
        self.reset_game()

    def reset_game(self):
        self.inning = 1
        self.is_top = True # True: 어웨이팀 공격, False: 홈팀 공격
        self.score_away = 0
        self.score_home = 0
        self.outs = 0
        self.strikes = 0
        self.balls = 0
        # 주자 상태: [1루, 2루, 3루]
        self.runners = [0, 0, 0]
        self.game_over = False

    def reset_at_bat(self):
        self.strikes = 0
        self.balls = 0

    def get_context_vector(self) -> np.ndarray:
        """
        강화학습 에이전트의 뇌(Context)에 들어갈 상태 벡터 (6D)
        [balls, strikes, outs, r1, r2, r3]
        """
        return np.array([
            self.balls / 3.0,
            self.strikes / 2.0,
            self.outs / 2.0,
            float(self.runners[0]),
            float(self.runners[1]),
            float(self.runners[2])
        ], dtype=np.float32)

    def process_pitch(self, 
                      swung: bool, 
                      contacted: bool, 
                      in_strike_zone: bool, 
                      exit_velocity_kmh: float = 0.0, 
                      distance_m: float = 0.0) -> Tuple[str, int]:
        """
        투구 결과를 처리하고 (이벤트 문자열, 발생한 득점) 반환
        """
        if self.game_over:
            return "Game Over", 0

        event = ""
        runs_scored = 0

        if contacted:
            # 타격 발생! 비거리와 속도로 휴리스틱 판정
            if distance_m < 2.0:
                event = "Foul"
                if self.strikes < 2:
                    self.strikes += 1
            else:
                event, runs_scored = self._resolve_hit(exit_velocity_kmh, distance_m)
        else:
            if swung:
                event = "Swinging Strike"
                self.strikes += 1
            else:
                if in_strike_zone:
                    event = "Called Strike"
                    self.strikes += 1
                else:
                    event = "Ball"
                    self.balls += 1

        # 볼넷 처리
        if self.balls >= 4:
            event = "Walk"
            runs_scored = self._advance_runners(1, force=True)
            self.reset_at_bat()

        # 삼진 처리
        if self.strikes >= 3:
            event = "Strikeout"
            self._add_out()

        # 이닝/게임 종료 체크 로직
        self._check_inning_state()
        
        # 득점 적용
        if self.is_top:
            self.score_away += runs_scored
        else:
            self.score_home += runs_scored

        return event, runs_scored

    def _resolve_hit(self, ev: float, dist: float) -> Tuple[str, int]:
        """비거리와 타구 속도로 안타/아웃 판정 및 주자 진루 처리"""
        # 단순 휴리스틱: 100km/h 이상 & 30m 이상이면 안타, 100m 이상이면 홈런
        if ev < 80.0 or dist < 20.0:
            self._add_out()
            return "Ground Out / Pop Out", 0
        
        runs = 0
        if dist >= 100.0:
            # 홈런
            runs = self._advance_runners(4) + 1 # 타자 본인 포함
            self.reset_at_bat()
            return "Home Run", runs
        elif dist >= 60.0:
            # 2루타
            runs = self._advance_runners(2)
            self.runners[1] = 1 # 타자는 2루로
            self.reset_at_bat()
            return "Double", runs
        else:
            # 단타
            runs = self._advance_runners(1)
            self.runners[0] = 1 # 타자는 1루로
            self.reset_at_bat()
            return "Single", runs

    def _advance_runners(self, bases: int, force: bool = False) -> int:
        runs = 0
        if force: # 볼넷 밀어내기
            if self.runners[0] == 1:
                if self.runners[1] == 1:
                    if self.runners[2] == 1:
                        runs += 1
                    self.runners[2] = 1
                self.runners[1] = 1
            self.runners[0] = 1
        else:
            # 일반 타격 시 진루
            new_runners = [0, 0, 0]
            for i in range(2, -1, -1):
                if self.runners[i] == 1:
                    next_base = i + bases
                    if next_base >= 3:
                        runs += 1
                    else:
                        new_runners[next_base] = 1
            self.runners = new_runners
        return runs

    def _add_out(self):
        self.outs += 1
        self.reset_at_bat()

    def _check_inning_state(self):
        if self.outs >= 3:
            self.outs = 0
            self.runners = [0, 0, 0]
            self.reset_at_bat()
            if self.is_top:
                self.is_top = False
            else:
                self.is_top = True
                self.inning += 1
                
                # 정규 이닝 종료 확인
                if self.inning > self.max_innings:
                    self.game_over = True
                # 9회말에 홈팀이 이기고 있으면 바로 종료
                elif self.inning == self.max_innings and not self.is_top and self.score_home > self.score_away:
                    self.game_over = True
