from irobot_edu_sdk.backend.bluetooth import Bluetooth
from irobot_edu_sdk.robots import event, hand_over, Color, Robot, Root, Create3
from irobot_edu_sdk.music import Note

from collections import deque

def createMazeDict(nXCells, nYCells, cellDim):
    mazeDict = {}
    for i in range(nXCells):
        for j in range(nYCells):
            cellsKey = (i, j)
            position = (i*cellDim, j*cellDim)
            neighbors = []
            visited = position in neighbors
            cost = 0
            mazeDict[cellsKey] = {'position': position, 'neighbors': neighbors, 'visited': visited, 'cost': cost}
    return mazeDict


def addAllNeighbors(mazeDict, nXCells, nYCells):
    for i in range(nXCells):
        for j in range(nYCells):
            cells = (i, j)
            neighborList = []

            if i - 1 >= 0:
                newi = i - 1
                neighborList.append((newi, j))

            if j + 1 <= len(range(nYCells))-1:
                newi = j + 1
                neighborList.append((i, newi))

            if i + 1 <= len(range(nXCells))-1:
                newi = i + 1
                neighborList.append((newi, j))

            if j - 1 >= 0:
                newi = j - 1
                neighborList.append((i, newi))
                
            mazeDict[cells]['neighbors'] += neighborList
    return mazeDict


def getRobotOrientation(heading):
    E = (0, 360)
    N = 90
    W = 180
    S = 270
    if (abs(heading - E[1]) < abs(N- heading) and abs(heading - E[1])<abs(heading - W) and abs(heading - E[1])<abs(S - heading)) or ((heading < abs(N- heading) and heading<abs(heading - W) and heading<abs(S - heading))):
        return "E"
    elif abs(N- heading) < abs(heading - W) and abs(N- heading) < abs(S - heading):
        return "N"
    elif abs(W - heading) < abs(S - heading):
        return "W"
    else:
        return "S"

def getPotentialNeighbors(currentCell, orientation):
    neighborList = []
    if orientation == "S":
        leftNeighbor = (currentCell[0]+1, currentCell[1])
        backNeighbor = (currentCell[0], currentCell[1]+1)
        frontNeighbor = (currentCell[0], currentCell[1]-1)
        rightNeighbor = (currentCell[0]-1, currentCell[1])

    if orientation == "N":
        leftNeighbor = (currentCell[0]-1, currentCell[1])
        backNeighbor = (currentCell[0], currentCell[1]-1)
        frontNeighbor = (currentCell[0], currentCell[1]+1)
        rightNeighbor = (currentCell[0]+1, currentCell[1])

    if orientation == "E":
        leftNeighbor = (currentCell[0], currentCell[1]+1)
        backNeighbor= (currentCell[0]-1, currentCell[1])
        frontNeighbor= (currentCell[0]+1, currentCell[1])
        rightNeighbor = (currentCell[0], currentCell[1]-1)

    if orientation == "W":
        leftNeighbor = (currentCell[0], currentCell[1]-1)
        backNeighbor= (currentCell[0]+1, currentCell[1])
        frontNeighbor= (currentCell[0]-1, currentCell[1])
        rightNeighbor = (currentCell[0], currentCell[1]+1)

    neighborList = [leftNeighbor, frontNeighbor, rightNeighbor, backNeighbor]
    return neighborList


def isValidCell(cellIndices, nXCells, nYCells):
    (current_x, current_y) = cellIndices
    inX = False
    inY = False
    if current_x >= 0 and current_x < nXCells:
        inX = True
    if current_y >= 0 and current_y < nYCells:
        inY = True
    if inX and inY:
        return True
    return False


def getWallConfiguration(IR0,IR3,IR6,threshold):
    proxList = []
    wallList= []
    leftProx = 4095/(IR0 + 1)
    frontProx = 4095/(IR3 + 1)
    rightProx = 4095/(IR6 + 1)
    proxList.append(leftProx)
    proxList.append(frontProx)
    proxList.append(rightProx)
    for prox in proxList:
        if prox <= threshold:
            wallList.append(True)
        else:
            wallList.append(False)
    return wallList


def getNavigableNeighbors(wallsAroundCell, potentialNeighbors, prevCell, nXCells, nYCells):
    # why does nXCells and nYCells matter at all?
    navNeighbors = []
    if prevCell != None:
        navNeighbors.append(prevCell)
    for i in range(len(wallsAroundCell)):
        if wallsAroundCell[i] == True:
            continue
        elif isValidCell(potentialNeighbors[i], nXCells, nYCells):
            navNeighbors.append(potentialNeighbors[i])
    return navNeighbors


def updateMazeNeighbors(mazeDict, currentCell, navNeighbors):
    for coordinate in mazeDict:
        if currentCell in mazeDict[coordinate]["neighbors"]:
            if coordinate not in navNeighbors:
                mazeDict[coordinate]["neighbors"].remove(currentCell)
    mazeDict[currentCell]["neighbors"] = navNeighbors
    return mazeDict


def getNextCell(mazeDict, currentCell):
    print("getting next cell")
    neighborList = mazeDict[currentCell]["neighbors"]
    notVisited = []
    haveVisited = []
    for coordinateTup in neighborList:
        if mazeDict[coordinateTup]["visited"] == False:
            notVisited.append(coordinateTup)
        else:
            haveVisited.append(coordinateTup)
    if len(notVisited) != 0:
        minCost = 0
        index = 0
        for i in range(len(notVisited)):
            if mazeDict[notVisited[i]]["cost"] < minCost:
                minCost = mazeDict[notVisited[i]]["cost"]
                index = i
        return notVisited[i]
    else:
        minCost = 0
        index = 0
        for i in range(len(haveVisited)):
            if mazeDict[haveVisited[i]]["cost"] < minCost:
                minCost = mazeDict[haveVisited[i]]["cost"]
                index = i
        return haveVisited[i]

def checkCellArrived(currentCell, destination):
    (current_x, current_y) = currentCell
    (desired_x, desired_y) = destination
    if current_x == desired_x and current_y == desired_y:
        return True
    return False

def updateMazeCost(mazeDict, start, goal):
    for (i,j) in mazeDict.keys():
        mazeDict[(i,j)]["flooded"] = False
    queue = deque([goal])
    mazeDict[goal]['cost'] = 0
    mazeDict[goal]['flooded'] = True
    while queue:
        current = queue.popleft()
        current_cost = mazeDict[current]['cost']
        for neighbor in mazeDict[current]['neighbors']:
            if not mazeDict[neighbor]['flooded']:
                mazeDict[neighbor]['flooded'] = True
                mazeDict[neighbor]['cost'] = current_cost + 1
                queue.append(neighbor)
    return mazeDict


def printMazeGrid(mazeDict, nXCells, nYCells, attribute):
    for y in range(nYCells - 1, -1, -1):
        row = '| '
        for x in range(nXCells):
            cell_value = mazeDict[(x, y)][attribute]
            row += '{} | '.format(cell_value)
        print(row[:-1])

# === CREATE ROBOT OBJECT
robot = Create3(Bluetooth("XJ-9"))

# === FLAG VARIABLES
HAS_COLLIDED = False
HAS_ARRIVED = False

# === BUILD MAZE DICTIONARY
N_X_CELLS = 3
N_Y_CELLS = 3
CELL_DIM = 50
MAZE_DICT = createMazeDict(N_X_CELLS, N_Y_CELLS, CELL_DIM)
MAZE_DICT = addAllNeighbors(MAZE_DICT, N_Y_CELLS, N_Y_CELLS)

# === DEFINING ORIGIN AND DESTINATION
PREV_CELL = (0,1)
START = (0,2)
CURR_CELL = START
DESTINATION = (2,2)
MAZE_DICT[CURR_CELL]["visited"] = True

# === PROXIMITY TOLERANCES
WALL_THRESHOLD = 120


# ==========================================================
# FAIL SAFE MECHANISMS

# EITHER BUTTON
@event(robot.when_touched, [True, True])  # User buttons: [(.), (..)]
async def when_either_button_touched(robot):
    global HAS_COLLIDED
    HAS_COLLIDED = True
    for i in range(50):
        await robot.set_wheel_speeds(0, 0)
        await robot.set_lights(Robot.LIGHT_ON,Color(255,0,0))


# EITHER BUMPER
@event(robot.when_bumped, [True, True])  # [left, right]
async def when_either_bumped(robot):
    global HAS_COLLIDED
    HAS_COLLIDED = True
    for i in range(50):
        await robot.set_wheel_speeds(0, 0)
        await robot.set_lights(Robot.LIGHT_ON,Color(255,0,0))


# ==========================================================
# MAZE NAVIGATION AND EXPLORATION

# === NAVIGATE TO CELL
async def navigateToNextCell(robot, nextCell, orientation):
    global MAZE_DICT, PREV_CELL, CURR_CELL, CELL_DIM
    neighborList = getPotentialNeighbors(CURR_CELL, orientation)
    i = 0
    for (index, coordinate) in enumerate(neighborList):
        if nextCell == coordinate:
            i = index
    if i == 0:
        await robot.turn_left(90)
        await robot.move(CELL_DIM)
    elif i == 1:
        await robot.move(CELL_DIM)
    elif i == 2:
        await robot.turn_right(90)
        await robot.move(CELL_DIM)
    else:
        await robot.turn_left(180)
        await robot.move(CELL_DIM)
    MAZE_DICT[CURR_CELL]["visited"] = True
    PREV_CELL = CURR_CELL
    CURR_CELL = nextCell

"""
WHERE DO WE USE ISVALIDCELL()??

what if we have it start as walls = [True, True, True]?
"""

# === EXPLORE MAZE
@event(robot.when_play)
async def navigateMaze(robot):
    global HAS_COLLIDED, HAS_ARRIVED
    global PREV_CELL, CURR_CELL, START, DESTINATION
    global MAZE_DICT, N_X_CELLS, N_Y_CELLS, CELL_DIM, WALL_THRESHOLD
    while HAS_COLLIDED == False and HAS_ARRIVED == False:
        ir_reading = (await robot.get_ir_proximity()).sensors
        pos = await robot.get_position()
        if checkCellArrived(CURR_CELL, DESTINATION) == True:
            await robot.set_wheel_speeds(0, 0)
            await robot.set_lights(Robot.LIGHT_SPIN, Color(0,255,0))
            break
        orientation = getRobotOrientation(pos.heading)
        wallsAroundCell = getWallConfiguration(ir_reading[0],ir_reading[3],ir_reading[6],WALL_THRESHOLD)
        potentialNeighbors = getPotentialNeighbors(CURR_CELL, orientation)
        neighbors = getNavigableNeighbors(wallsAroundCell, potentialNeighbors, PREV_CELL, N_X_CELLS, N_Y_CELLS)
        print("nav neighbors",neighbors)
        MAZE_DICT = updateMazeNeighbors(MAZE_DICT, CURR_CELL, neighbors)
        MAZE_DICT = updateMazeCost(MAZE_DICT, START, DESTINATION)
        print("c")
        nextCell = getNextCell(MAZE_DICT, CURR_CELL)
        print("nextCell",nextCell)
        await navigateToNextCell(robot, nextCell, orientation)

# start the robot
robot.play()
