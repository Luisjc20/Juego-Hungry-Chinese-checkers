from game_logic.player import Player
from game_logic.game import *
from game_logic.helpers import add, mult

class CustomBotTemplate(Player):
    def __init__(self):
        super().__init__()
    
    def pickMove(self, g:Game):
        moves = g.allMovesDict(self.playerNum)
        
        """
        Realiza movimientos aleatorios
        """
        from random import choice
        l = []
        for coor in moves:
            if moves[coor] != []: l.append(coor)
        start = choice(l)
        end = choice(moves[start])
        return [subj_to_obj_coor(start, self.playerNum),
                subj_to_obj_coor(end, self.playerNum)]
