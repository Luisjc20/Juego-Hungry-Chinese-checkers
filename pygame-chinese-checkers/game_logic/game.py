from .literals import *
from .helpers import *
from .piece import *
import pygame, copy

class Game:
    def __init__(self, playerCount=3):
        if playerCount in (2,3): self.playerCount = playerCount
        else: self.playerCount = 3
        self.pieces: dict[int, set[Piece]] = {1:set(), 2:set(), 3:set()}
        self.board = self.createBoard(playerCount)
        
        self.unitLength = int(WIDTH * 0.05) 
        self.lineWidth = int(self.unitLength * 0.05) 
        self.circleRadius = int(HEIGHT * 0.025) 
        self.centerCoor = (WIDTH/2, HEIGHT/2) #tamaño de ventana 800*600

    def createBoard(self, playerCount: int):
        Board = {}
        #Fin de la zona del jugador 1
        for p in range(-4,1):
            for q in range(4,9):
                if p + q > 4: continue
                else: 
                    if (p,q) not in Board: Board[(p,q)] = None
        #Inicio de la zona del jugador 1
        for p in range(0,5):
            for q in range(-8,-3):
                if p + q < -4: continue
                else: 
                    Board[(p,q)] = Piece(1, p, q)
                    self.pieces[1].add(Board[p, q])
        #Fin de la zona del jugador 2
        for p in range(4,9):
            for q in range(-4,1):
                if p + q > 4: continue
                else: 
                    if (p,q) not in Board: Board[(p,q)] = None
        #Inicio de la zona del jugador 1
        for p in range(-8,-3):
            for q in range(0,5):
                if p + q < -4: continue
                else: 
                    Board[(p,q)] = Piece(2, p, q)
                    self.pieces[2].add(Board[p, q])
        #Fin de la zona del jugador 2
        for p in range(-4,1):
            for q in range(-4,1):
                if p + q > -4: continue
                else:
                    if (p,q) not in Board: Board[(p,q)] = None
        #Inicio de la zona del jugador 1
        for p in range(0,5):
            for q in range(0,5):
                if p + q < 4: continue
                else:
                    Board[(p,q)] = None if playerCount == 2 else Piece(3, p, q)
                    if playerCount == 3: self.pieces[3].add(Board[p, q])
        #Zona neutra
        for p in range(-3,4):
            for q in range(-3,4):
                if p + q <= 3 and p + q >= -3: Board[(p,q)] = None
        return Board

    def getValidMoves(self, startPos: tuple, playerNum: int):
        
        moves = []
        for direction in DIRECTIONS:
            destination = add(startPos, direction)
            if destination not in self.board: continue #fuera de los límites
            elif self.board[destination] == None: moves.append(destination) #caminar
            else: 
                destination = add(destination, direction)
                if destination not in self.board or self.board[destination] != None: continue #fuera de los límites o no puedo saltar
                moves.append(destination)
                checkJump(moves, self.board, destination, direction, playerNum)
        for i in copy.deepcopy(moves):
            #Puedes pasar del territorio de otro jugador, pero no puedes quedarte allí.
            if (i not in START_COOR[playerNum]) and (i not in END_COOR[playerNum]) and (i not in NEUTRAL_COOR):
                while i in moves:
                    moves.remove(i)
        return list(set(moves))

    def checkWin(self, playerNum: int):
        for i in END_COOR[playerNum]:
            if self.board[i] == None: return False
            if isinstance(self.board[i], Piece) and self.board[i].getPlayerNum() != playerNum: return False
        return True

    def getBoardState(self, playerNum: int):
        
        state = dict()
        for i in self.board:
            state[obj_to_subj_coor(i, playerNum)] = (0 if self.board[i] == None else int(self.board[i].getPlayerNum()))
        return state
    
    def getBoolBoardState(self, playerNum: int):
        
        state = dict()
        for i in self.board:
            state[obj_to_subj_coor(i, playerNum)] = (self.board[i] != None)
        return state

    def allMovesDict(self, playerNum: int):
        '''Devuelve los movimientos válidos'''
        moves = dict()
        for p in self.pieces[playerNum]:
            p_moves_list = self.getValidMoves(p.getCoor(), playerNum)
            if p_moves_list == []: continue
            p_subj_coor = obj_to_subj_coor(p.getCoor(), playerNum)
            moves[p_subj_coor] = [obj_to_subj_coor(i, playerNum) for i in p_moves_list]
        return moves

    def movePiece(self, start: tuple, end: tuple):
        assert self.board[start] != None and self.board[end] == None, "AssertionError at movePiece()"
        self.board[start].setCoor(end)
        self.board[end] = self.board[start]
        self.board[start] = None

    def drawBoard(self, window: pygame.Surface, playerNum: int=1):
        
        self.drawPolygons(window, playerNum)
        self.drawLines(window)
        self.drawCircles(window, playerNum)

    def drawCircles(self, window:pygame.Surface, playerNum: int):
        for obj_coor in self.board:
            coor = obj_to_subj_coor(obj_coor, playerNum)
            c = add(self.centerCoor, mult(h2c(coor),self.unitLength)) #coordenadas absolutas en pantalla
            pygame.draw.circle(window, WHITE, c, self.circleRadius)
            pygame.draw.circle(window, BLACK, c, self.circleRadius, self.lineWidth)
            if isinstance(self.board[obj_coor], Piece):
                pygame.draw.circle(window, PLAYER_COLORS[self.board[obj_coor].getPlayerNum()-1], c, self.circleRadius-2)
           

    def drawLines(self, window: pygame.Surface):
        
        visited = set()
        neighbors = set()
        for coor in self.board:
            for dir in DIRECTIONS:
                n_coor = add(coor,dir)
                if n_coor not in visited and n_coor in self.board:
                    neighbors.add(n_coor)
            for n_coor in neighbors:
                c = add(self.centerCoor, mult(h2c(coor),self.unitLength))
                n = add(self.centerCoor, mult(h2c(n_coor),self.unitLength))
                pygame.draw.line(window, BLACK, c, n, self.lineWidth)
            neighbors.clear()
        

    def drawPolygons(self, window: pygame.Surface, playerNum: int=1):
        #centro del hexagono
        pygame.draw.polygon(window, WHITE, (abs_coors(self.centerCoor, (-4,4), self.unitLength), abs_coors(self.centerCoor, (0,4), self.unitLength), abs_coors(self.centerCoor, (4,0), self.unitLength), abs_coors(self.centerCoor, (4,-4), self.unitLength), abs_coors(self.centerCoor, (0,-4), self.unitLength), abs_coors(self.centerCoor, (-4,0), self.unitLength)))
        #triangulos
        if playerNum == 1: colors = (YELLOW, RED, GREEN)
        elif playerNum == 2: colors = (RED, GREEN, YELLOW)
        elif playerNum == 3: colors = (GREEN, YELLOW, RED)
        pygame.draw.polygon(window, colors[0], (add(self.centerCoor,mult(h2c((-4,8)), self.unitLength)), add(self.centerCoor,mult(h2c((-4,4)), self.unitLength)), add(self.centerCoor,mult(h2c((0,4)), self.unitLength))))
        pygame.draw.polygon(window, colors[0], (add(self.centerCoor,mult(h2c((0,-4)), self.unitLength)), add(self.centerCoor,mult(h2c((4,-4)), self.unitLength)), add(self.centerCoor,mult(h2c((4,-8)), self.unitLength))))
        pygame.draw.polygon(window, colors[2], (add(self.centerCoor,mult(h2c((-4,0)), self.unitLength)), add(self.centerCoor,mult(h2c((-4,-4)), self.unitLength)), add(self.centerCoor,mult(h2c((0,-4)), self.unitLength))))
        pygame.draw.polygon(window, colors[2], (add(self.centerCoor,mult(h2c((0,4)), self.unitLength)), add(self.centerCoor,mult(h2c((4,4)), self.unitLength)), add(self.centerCoor,mult(h2c((4,0)), self.unitLength))))
        pygame.draw.polygon(window, colors[1], (add(self.centerCoor,mult(h2c((4,0)), self.unitLength)), add(self.centerCoor,mult(h2c((8,-4)), self.unitLength)), add(self.centerCoor,mult(h2c((4,-4)), self.unitLength))))
        pygame.draw.polygon(window, colors[1], (add(self.centerCoor,mult(h2c((-8,4)), self.unitLength)), add(self.centerCoor,mult(h2c((-4,4)), self.unitLength)), add(self.centerCoor,mult(h2c((-4,0)), self.unitLength))))

