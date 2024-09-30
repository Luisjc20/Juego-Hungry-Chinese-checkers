from .game import *
from .piece import *
from .literals import *
from .helpers import *
import random
import pygame
import math
from pygame.locals import *
import sys
from abc import ABC, ABCMeta, abstractmethod

class PlayerMeta(ABCMeta):
    playerTypes = []

    def __init__(cls, name, bases, attrs):
        if ABC not in bases:
            PlayerMeta.playerTypes.append(cls)
        super().__init__(name, bases, attrs)

class Player(ABC, metaclass=PlayerMeta):
    def __init__(self):
        self.playerNum = 0
        self.has_won = False
    def getPlayerNum(self):
        return self.playerNum
    def setPlayerNum(self, num: int):
        self.playerNum = num
    
    @abstractmethod
    def pickMove(self, g:Game):
        ...

class RandomBotPlayer(Player):
    def __init__(self):
        super().__init__()
    
    def pickMove(self, g: Game):
        '''returns [start_coor, end_coor]'''
        moves = g.allMovesDict(self.playerNum)
        l = []
        for coor in moves:
            if moves[coor] != []: l.append(coor)
        coor = random.choice(l)
        move = random.choice(moves[coor])
        return [subj_to_obj_coor(coor, self.playerNum), subj_to_obj_coor(move, self.playerNum)]

class MinimaxBotPlayer(Player):
    def __init__(self, depth=3):
        super().__init__()
        self.depth = depth  # Profundidad de búsqueda

    def pickMove(self, g: Game):
        '''returns [start_coor, end_coor]'''
        best_move = None
        best_value = float('-inf')  # Inicializar con el peor valor posible para maximizar

        moves = g.allMovesDict(self.playerNum)  # Obtener todos los movimientos posibles
        for start, ends in moves.items():
            for end in ends:
                # Realizar el movimiento y evaluar su valor
                g.makeMove(start, end)
                move_value = self.minimax(g, self.depth - 1, False)  # Comienza como False para minimizar
                g.undoMove()  # Deshacer movimiento

                # Comparar y almacenar el mejor movimiento
                if move_value > best_value:
                    best_value = move_value
                    best_move = [start, end]

        return best_move

    def minimax(self, g: Game, depth: int, is_maximizing: bool):
        """
        Implementa el algoritmo Minimax.
        :param g: Estado actual del juego (Game).
        :param depth: Profundidad de búsqueda actual.
        :param is_maximizing: True si estamos maximizando, False si minimizando.
        :return: Valor del movimiento.
        """
        if depth == 0 or g.isGameOver():
            return self.evaluateBoard(g)

        if is_maximizing:
            max_eval = float('-inf')
            moves = g.allMovesDict(self.playerNum)
            for start, ends in moves.items():
                for end in ends:
                    g.makeMove(start, end)
                    eval = self.minimax(g, depth - 1, False)  # Minimizar en el siguiente paso
                    g.undoMove()
                    max_eval = max(max_eval, eval)
            return max_eval
        else:
            min_eval = float('inf')
            moves = g.allMovesDict(self.getOpponentNum())  # Obtener movimientos del oponente
            for start, ends in moves.items():
                for end in ends:
                    g.makeMove(start, end)
                    eval = self.minimax(g, depth - 1, True)  # Maximizar en el siguiente paso
                    g.undoMove()
                    min_eval = min(min_eval, eval)
            return min_eval

    def evaluateBoard(self, g: Game):
        """
        Función de evaluación del tablero.
        Debe devolver un valor numérico que representa la ventaja del bot en el estado actual del juego.
        :param g: Estado actual del juego (Game).
        :return: Valor numérico que representa el estado del juego.
        """
        # Aquí se define una simple función de evaluación:
        # +10 por cada ficha propia más cerca del triángulo opuesto,
        # -10 por cada ficha enemiga más cerca de nuestro triángulo inicial.
        value = 0
        my_fichas = g.getPlayerPositions(self.playerNum)
        opponent_fichas = g.getPlayerPositions(self.getOpponentNum())

        # Evaluar las posiciones de nuestras fichas
        for ficha in my_fichas:
            value += (ficha[1] - 0)  # Valoración simple de distancia al centro

        # Evaluar las posiciones de las fichas enemigas
        for ficha in opponent_fichas:
            value -= (ficha[1] - 0)  # Penalizar posiciones enemigas más cercanas a nuestro lado

        return value

    def getOpponentNum(self):
        """
        Retorna el número del oponente.
        :return: Número del oponente.
        """
        return 1 if self.playerNum == 2 else 2

class BotPrimeroElMejor(Player):
    '''Siempre encuentra el primer movimiento disponible, priorizando los movimientos hacia delante.'''
    def __init__(self):
        super().__init__()

    def pickMove(self, g: Game):
        '''devuelve [start_coor, end_coor] en coordenadas objetivas'''
        moves = g.allMovesDict(self.playerNum)
        forwardMoves = dict()
        sidewaysMoves = dict()
        start_coor = ()
        end_coor = ()

        # Split moves into forward and sideways
        for coor in moves:
            if moves[coor] != []:
                for dest in moves[coor]:
                    if dest[1] > coor[1]:  # Forward move
                        forwardMoves.setdefault(coor, []).append(dest)
                    if dest[1] == coor[1]:  # Sideways move
                        sidewaysMoves.setdefault(coor, []).append(dest)

        # Check for forward moves first
        if forwardMoves:
            start_coor = next(iter(forwardMoves))  # Get the first key (start coordinate)
            end_coor = forwardMoves[start_coor][0]  # Get the first destination
        else:  # If no forward moves, look for sideways moves
            if sidewaysMoves:
                start_coor = next(iter(sidewaysMoves))  # Get the first key (start coordinate)
                end_coor = sidewaysMoves[start_coor][0]  # Get the first destination

        return [subj_to_obj_coor(start_coor, self.playerNum), subj_to_obj_coor(end_coor, self.playerNum)]

class HumanPlayer(Player):
    def __init__(self):
        super().__init__()
    
    def pickMove(self, g:Game, window:pygame.Surface, humanPlayerNum: int=0, highlight=None):
        pieceSet:set[Piece] = g.pieces[self.playerNum]
        validmoves = []
        clicking = False
        selected_piece_coor = ()
        prev_selected_piece_coor = ()
        
        while True:
            ev = pygame.event.wait()
            if ev.type == QUIT:
                pygame.quit()
                sys.exit() 
            
            #espera un clic,
            #si el mouse pasa sobre una pieza, se resalta
            mouse_pos = pygame.mouse.get_pos()
            clicking = ev.type == MOUSEBUTTONDOWN
            #
            if highlight:
                pygame.draw.circle(window, (117,10,199), abs_coors(g.centerCoor, highlight[0], g.unitLength), g.circleRadius, g.lineWidth+2)
                pygame.draw.circle(window, (117,10,199), abs_coors(g.centerCoor, highlight[1], g.unitLength), g.circleRadius, g.lineWidth+2)

            backButton = TextButton('Regresar al menú', width=int(HEIGHT*0.25), height=int(HEIGHT*0.0833), font_size=int(WIDTH*0.04))
            if backButton.isClicked(mouse_pos, clicking):
                return (False, False)
            backButton.draw(window, mouse_pos)

            for piece in pieceSet:
                coor = obj_to_subj_coor(piece.getCoor(), self.playerNum) if humanPlayerNum != 0 else piece.getCoor()
                absCoor = abs_coors(g.centerCoor, coor, g.unitLength)
                if math.dist(mouse_pos, absCoor) <= g.circleRadius and piece.mouse_hovering == False:
                    #cambiar el color de la pieza
                    pygame.draw.circle(window, brighten_color(PLAYER_COLORS[piece.getPlayerNum()-1], 0.75), absCoor, g.circleRadius-2)
                    piece.mouse_hovering = True
                elif math.dist(mouse_pos, absCoor) > g.circleRadius and piece.mouse_hovering == True and tuple(window.get_at(ints(absCoor))) != WHITE:
                    #dibuja un circulo del color original
                    pygame.draw.circle(window, PLAYER_COLORS[piece.getPlayerNum()-1], absCoor, g.circleRadius-2)
                    piece.mouse_hovering = False
                #cuando se selecciona una pieza y haces clic en cualquiera de los destinos válidos,
                # moverás esa pieza al destino
                if selected_piece_coor == piece.getCoor() and validmoves != []:
                    for d in validmoves:
                        destCoor = abs_coors(g.centerCoor, obj_to_subj_coor(d, self.playerNum), g.unitLength) if humanPlayerNum != 0 else abs_coors(g.centerCoor, d, g.unitLength)
                        if math.dist(mouse_pos, destCoor) <= g.circleRadius:
                            if clicking:
                                return [selected_piece_coor, d]
                            #se dibuja un circulo gris
                            else: pygame.draw.circle(window, LIGHT_GRAY, destCoor, g.circleRadius-2)
                        elif math.dist(mouse_pos, destCoor) > g.circleRadius:
                            #se dibuja un circulo blanco
                            pygame.draw.circle(window, WHITE, destCoor, g.circleRadius-2)
                #dando click en la pieza
                if math.dist(mouse_pos, absCoor) <= g.circleRadius and clicking == True:
                    selected_piece_coor = piece.getCoor()
                    if prev_selected_piece_coor != () and selected_piece_coor != prev_selected_piece_coor:
                        if humanPlayerNum != 0: g.drawBoard(window, self.playerNum)
                        else: g.drawBoard(window)
                    prev_selected_piece_coor = selected_piece_coor
                    #dibuja un círculo gris semitransparente fuera de la pieza
                    pygame.draw.circle(window, (161,166,196,50), absCoor, g.circleRadius, g.lineWidth+1)
                    #dibuja círculos semitransparentes alrededor de todas las coordenadas en getValidMoves()
                    validmoves = g.getValidMoves(selected_piece_coor, self.playerNum)
                for c in validmoves:
                    c2 = obj_to_subj_coor(c, self.playerNum) if humanPlayerNum != 0 else c
                    pygame.draw.circle(window, (161,166,196), abs_coors(g.centerCoor, c2, g.unitLength), g.circleRadius, g.lineWidth+2)

            pygame.display.update()
            
