import matplotlib.pyplot as plt
import pygame
import json
import math
import random
from a_star import AStarPlanner
from pygame_gui import UIManager
import pygame_gui
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

class Background(pygame.sprite.Sprite):
    def __init__(self, image, location):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(image)
        self.rect = self.image.get_rect()
        self.rect.topleft = location

pygame.init()
MAP_SIZE_COEFF = 5.14
loaded_image = pygame.image.load('image (3).png')
image_width = loaded_image.get_width()
image_height = loaded_image.get_height()
space_width = 50
screen = pygame.display.set_mode([image_width , image_height + space_width])
screen.fill((255, 255, 255))
running = True
ui_manager = UIManager((image_width, image_height + space_width))

bground = Background('image (3).png', (0, 0))
scale_x = image_width / screen.get_width()
scale_y = image_height / (screen.get_height( ) - space_width)
scale = max(scale_x, scale_y)
scaled_width = int(image_width / scale)
scaled_height = int(image_height / scale)
bground.image = pygame.transform.scale(bground.image, (scaled_width, scaled_height))
screen.blit(bground.image, bground.rect)

gen_route = [] # nothing one just for the generate route button
path_wp = [] # manual path coordinate drawn
obstacles_wp = [] # obstacle coordinate drawn
auto_wp = [] # n number of auto path coordinate generated
auto_routes = [] # coordinates on the route line generated
ox, oy = [], [] # (obstacles) all coordinates in a straight line of the border + coordinates drawn manually 
start_points = [(746, 320), (746, 347), (746, 374), (746, 401), (746, 428), (746, 455)]
final_routes = []
def get_dist_btw_pos(pos0, pos1):
    """
    Get distance between 2 mouse position.
    """
    x = abs(pos0[0] - pos1[0])
    y = abs(pos0[1] - pos1[1])
    dist_px = math.hypot(x, y)
    dist_cm = dist_px * MAP_SIZE_COEFF
    return int(dist_cm), int(dist_px)
def get_angle_btw_line(pos0, pos1, posref, twopoints):
    """
    Get angle between two lines respective to 'posref'
    NOTE: using dot product calculation.
    """
    ax = posref[0] - pos0[0]
    ay = posref[1] - pos0[1]
    bx = posref[0] - pos1[0]
    by = posref[1] - pos1[1]
    # Get dot product of pos0 and pos1.
    _dot = (ax * bx) + (ay * by)
    # Get magnitude of pos0 and pos1.
    _magA = math.sqrt(ax**2 + ay**2)
    _magB = math.sqrt(bx**2 + by**2)
    try:
        _rad = math.acos(_dot / (_magA * _magB))
    # Angle in degrees.
        if twopoints:
            angle = (_rad * 180) / math.pi
        else:
            angle = 180 - ((_rad * 180) / math.pi)
    except ValueError:
        print('next')
        return "NA"
    return int(angle)

def remove_coordinates(route):
    if len(route) < 3:
        return route
    filtered = []
    filtered.append(route[0])
    prevgradient = 0
    for i in range(1,len(route)):
        # print(route[i])
        if route[i][0] == route[i-1][0]: #if route is straight (x axis is same) --> |
            filtered.append(route[i])

        elif route[i][1] != route[i-1][1]: #if route is going downwards (yaxis diff) --> /
            x1 = route[i][0]
            y1 = route[i][1]
            x2 = route[i-1][0]
            y2 = route[i-1][1]
            if x2-x1 != 0:
                gradientcalc = (y2 - y1) / (x2 - x1)
            if gradientcalc != prevgradient:
                filtered.append(route[i])
                prevgradient = gradientcalc
            else:
                filtered.pop()
                filtered.append(route[i])
        elif i + 1 != len(route): 
            if route[i][1] == route[i-1][1] and route[i][1] != route[i+1][1]: 
                filtered.append(route[i])
            
        elif i + 1 == len(route): #last point
            filtered.append(route[i])
    print(filtered[::-1])
    return filtered[::-1]

def calculate_angle(auto_routes): 
    details = {}
    i=0
    for pxroute in auto_routes:
        i+=1
        details[i] = []   #details = {1: []}
        if len(pxroute) == 2:
            # print(pxroute)
            # route = convert_route_to_real_life(pxroute)
            # print('-----')
            movement_details = [] #detail for one specific movement consisting of [direction, angle, route waypoint]
            start = pxroute[0]
            end = pxroute[1] #(x,y)
            if end[1] > start[1]:  #direction of movement
                movement_details.append("ccw")
            elif end[1] < start[1]:
                movement_details.append("cw")
            else:
                movement_details.append("s")
            posref = (end[0], start[1])
            angle_deg = get_angle_btw_line(end, posref, start, True)
            distance,_ = get_dist_btw_pos(pxroute[0], pxroute[1])
            movement_details.append(angle_deg) 
            movement_details.append(distance)  # append route waypoint 
            details[i].append(movement_details)
                
        elif len(pxroute) > 2:
            # filteredroute = remove_coordinates(pxroute)
            print(pxroute)
            previousdirection = ""
            for j in range(len(pxroute)-1):
                if j == len(pxroute) -1:
                    break
                movement_details = [] #detail for one specific movement consisting of [direction, angle, route waypoint]
                start = pxroute[j]
                end = pxroute[j+1] #(x,y)
                if j == 0 and start[1] == end[1]:
                    movement_details.append("s")
                    previousdirection = "s"
                    movement_details.append(0)
                else: 
                    if angle_deg == "NA":
                        break
                    distance,_ = get_dist_btw_pos(pxroute[j], pxroute[j+1])
                    movement_details.append("ccw")
                    previousdirection = "ccw"
                    angle = get_angle_btw_line(pxroute[j-1], pxroute[j+1], pxroute[j], False)
                    print(angle)
                    movement_details.append(angle)
                movement_details.append(distance)  # append route waypoint 
                details[i].append(movement_details)
    print(details)
    return details  #{droneid:[ [movement details 1],[movement details 2] ], droneid: [ [movement details 1],[movement details 2] ]}


# def submit():
#     global auto_routes
#     finaloutput = calculate_angle(auto_routes) #get angle and direction from startpoint and endpoint and edit the json 
#     # totalroutes = len(final_routes)
#     f = open('waypoint.json', 'w+')
#     json.dump(finaloutput, f, indent=0)
#     f.close()
#     return 
def submit():
    global auto_routes
    final_output = calculate_angle(auto_routes)  # get angle and direction from startpoint and endpoint

    with open('waypoint.txt', 'w+') as f:
        for drone_id, movement_details_list in final_output.items():
            for movement_details in movement_details_list:
                direction = movement_details[0]
                angle = movement_details[1]
                distance = movement_details[2]
                # if direction == 'cw':
                #     f.write(f"{drone_id}>")
                #     f.write(f"{direction} {angle}\n")
                #     f.write(f"{drone_id}>forward {distance}\n")

                #     f.write(f"{drone_id}>")
                #     f.write(f"ccw {angle}\n")
                # elif direction == 'ccw':
                #     f.write(f"{drone_id}>")
                #     f.write(f"{direction} {angle}\n")
                #     f.write(f"{drone_id}>forward {distance}\n")
                #     f.write(f"{drone_id}>")
                #     f.write(f"cw {angle}\n")
                # else:
                #     f.write(f"{drone_id}>forward {distance}\n")
                if direction != 's':
                    f.write(f"{drone_id}>")
                    f.write(f"{direction} {angle}\n")
                f.write(f"{drone_id}>forward {distance}\n")
            f.write("\n")

def draw_point(position):
    pygame.draw.circle(screen, (255, 0, 0), position, 5)  # Draws a red circle at the given position with a radius of 5 pixels

def draw_lines(points, color):
    for i in range(len(points) - 1):
        pygame.draw.line(screen, color, points[i], points[i+1], 2)

def get_points_on_line(p1,p2):
    global ox
    global oy
    x0, y0 = p1
    x1, y1 = p2
    points = [p1,p2]
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    err = dx - dy
    while True:
        ox.append(x0)
        oy.append(y0)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return points

def is_obstacle_in_path(start, end, obstacle_x, obstacle_y):
    x1, y1 = start
    x2, y2 = end

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    dx2 = 2 * dx
    dy2 = 2 * dy

    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1

    err = dx - dy

    x, y = x1, y1

    while x != x2 or y != y2:
        if x in obstacle_x and y in obstacle_y:
            obstacle_index = obstacle_x.index(x)
            if obstacle_y[obstacle_index] == y:
                return True

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

    if x in obstacle_x and y in obstacle_y:
        obstacle_index = obstacle_x.index(x)
        if obstacle_y[obstacle_index] == y:
            return True

    return False
def manual_plan(event):
    global manualmode
    global path_wp
    if event.type == pygame.QUIT:
        manualmode = False
    elif event.type == pygame_gui.UI_BUTTON_PRESSED:
        manualmode = False
    elif event.type == pygame.MOUSEBUTTONDOWN:
        pos = pygame.mouse.get_pos()
        if pos[1] < image_height:
            path_wp.append(pos)
            print(pos)
            draw_point(pos)
            if len(path_wp) > 1:
                pygame.draw.line(screen, 'green', path_wp[-2], path_wp[-1], 2)
    ui_manager.process_events(event)
    ui_manager.update(1/60)  # Update the UI manager
    ui_manager.draw_ui(screen)  # Draw the UI components
    pygame.display.update()
def is_point_inside_polygon(x, y, polygon):
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside
def generate_random_points(n_times):
    global auto_wp
    global ox
    global oy
    # polygon_vertices =[(746, 266), (746, 459), (395, 459), (395, 541), (103, 541), (103, 266) ]
    # polygon = Polygon(polygon_vertices)

    # while n_times > 0:
    #     while True:
    #         rand_x = random.randint(0, image_width)
    #         rand_y = random.randint(0, image_height)
    #         point = Point(rand_x, rand_y)

    #         if polygon.contains(point):
    #             auto_wp.append((rand_x, rand_y))
    #             break
    #     n_times -= 1
    specific_areas = [[(130, 320), (130, 525), (253, 421)],
                      [(130,320), (253,421),(577,320)],
                      [(130, 525),(253,421),(395,525)],
                      [(253,421),(395,320),(395,525)],
                      [(395,320),(577,320), (577,386),(395,386)],
                      [(395,386), (577,386), (577,459),(395,459)]
                      ]
    while n_times > 0:
        while True:
            rand_x = random.randint(130, 577)
            rand_y = random.randint(320,525)
            ox.append(rand_x)
            oy.append(rand_y)
            point = Point(rand_x, rand_y)
            polygon = Polygon(specific_areas[n_times-1])
            if polygon.contains(point):
                auto_wp.append((rand_x, rand_y))
                break
        n_times -= 1
    print(auto_wp)
def do_lines_intersect(line1_start, line1_end, line2_start, line2_end):
    x1, y1 = line1_start
    x2, y2 = line1_end
    x3, y3 = line2_start
    x4, y4 = line2_end

    # Calculate the orientation of three points
    def calculate_orientation(x1, y1, x2, y2, x3, y3):
        return (y2 - y1) * (x3 - x2) - (y3 - y2) * (x2 - x1)

    # Check if the orientations of the endpoints are different
    if (calculate_orientation(x1, y1, x2, y2, x3, y3) > 0) != (calculate_orientation(x1, y1, x2, y2, x4, y4) > 0) and \
       (calculate_orientation(x3, y3, x4, y4, x1, y1) > 0) != (calculate_orientation(x3, y3, x4, y4, x2, y2) > 0):
        return True  # The lines intersect

    return False  # The lines do not intersect

def check_line_intersections(lines):
    for i in range(len(lines)):
        line1 = lines[i]
        if len(line1) != 2:
            continue

        line1_start, line1_end = line1

        for j in range(i + 1, len(lines)):
            line2 = lines[j]
            if len(line2) != 2:
                continue

            line2_start, line2_end = line2

            if do_lines_intersect(line1_start, line1_end, line2_start, line2_end):
                # Swap the endpoints
                
                lines[i] = [line1_start, line2_end]
                lines[j] = [line2_start, line1_end]

    return lines

def convert_to_real_life(pixel_waypoint):
    """
    Convert computer pixel waypoint to real-life distance.
    """
    x = pixel_waypoint[0] * MAP_SIZE_COEFF
    y = pixel_waypoint[1] * MAP_SIZE_COEFF
    real_life_distance = (x, y)
    return real_life_distance

def convert_route_to_real_life(route):
    """
    Convert a route from pixel waypoints to real-life points.
    """
    converted_route = []
    for waypoint_pair in route:
        # converted_pair = []
        converted_pair = convert_to_real_life(waypoint_pair)
        # for waypoint in waypoint_pair:
        #     real_life_point = convert_to_real_life(waypoint)
        #     converted_pair.append(real_life_point)
        converted_route.append(converted_pair)
    return converted_route                                                                                                                                                                                                                                                                                                                                                                     

def auto_plan():
    global auto_routes 
    global start_points
    global final_routes
    n_times = 6
    generate_random_points(n_times)
    copied_list = auto_wp[:]
    grid_size = 15
    robot_radius = 1
    # try:
    for i in range(len(auto_wp)):
        index_of_min = 0
        if len(copied_list) > 1:
            index_of_min = min(enumerate(copied_list), key=lambda x: x[1][1])[0] #assigning drones to nearest endpoints based on the y axis
        # if is_obstacle_in_path(start, copied_list[index_of_min], ox, oy) == True:
        if copied_list[index_of_min][1] > 469:
            a_star = AStarPlanner(ox, oy, grid_size, robot_radius)
            rx, ry = a_star.planning(start_points[i][0], start_points[i][1], copied_list[index_of_min][0], copied_list[index_of_min][1])
            points = list(zip(rx, ry))
            filtered = remove_coordinates(points)
            auto_routes.append(filtered)
        else:     
            auto_routes.append([start_points[i], copied_list[index_of_min]])
        
        del copied_list[index_of_min]
    auto_routes = check_line_intersections(auto_routes) #this switches endpoints for drones that have intersecting routes 
    # except IndexError:
    #     print("Try again")
    #     return 
    print(auto_routes)
    # for route in auto_routes: #switching routes in pixels to real life 
    #     converted_route = convert_route_to_real_life(route)
    #     final_routes.append(converted_route)
    # print(final_routes)


def generate_route(): #to print auto routes on the map after button
    global auto_routes
    global gen_route
    gen_route = auto_routes
    submit()


auto_plan_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, image_height + 10), (100, 30)),
                                      text="Auto Plan",
                                      manager=ui_manager)
auto_plan_btn.callback = lambda: auto_plan
generate_route_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((210, image_height + 10), (100, 30)),
                                      text="Generate Plan",
                                      manager=ui_manager)
generate_route_btn.callback = lambda: generate_route
manual_plan_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((360, image_height + 10), (100, 30)),
                                      text="Manual Plan",
                                      manager=ui_manager)
manual_plan_btn.callback = lambda: manual_plan

top = get_points_on_line((110, 290),(766, 290))
left = get_points_on_line((110, 290),(110, 561))
bottom = get_points_on_line((110, 561),(766, 561))
right = get_points_on_line((766, 290), (766, 561))
wall3 = get_points_on_line((746, 469), (395, 469))
wall4 = get_points_on_line((395, 469), (395, 525))

manualmode = False

while running:
    index = 0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == auto_plan_btn:
                auto_plan()
            elif event.ui_element == generate_route_btn:
                generate_route()
            elif event.ui_element == manual_plan_btn:
                manualmode = True
                while manualmode:
                    for event in pygame.event.get():
                        manual_plan(event)
        ui_manager.process_events(event)
             
    ui_manager.update(1/60)  # Update the UI manager
    screen.blit(bground.image, bground.rect)
    ui_manager.draw_ui(screen)  # Draw the UI components
    draw_lines(path_wp, 'green')

    for i in range(len(auto_wp)):
        pygame.draw.circle(screen, (255, 0, 0), auto_wp[i], 5)

    for i in range(len(start_points)):
        pygame.draw.circle(screen, (255, 0, 0), start_points[i], 5)

    movingarea = [(746, 320), (746, 469), (395, 469), (395, 525), (130, 525), (130, 320),(746, 320),(577, 320),(577, 469)]
    for i in range(len(movingarea)):
        pygame.draw.lines(screen, 'blue', False, movingarea, 2) 
#     test = [(740, 425), (290, 425), (260, 440), (230, 455), (185, 470), (170, 485)]
# #[(740, 455), (290, 455), (260, 470), (230, 485), (185, 500), (170, 515)]
#     # test = [(320, 515), (335, 500), (350, 500), (395, 455), (740, 455)]
#     for i in range(len(test)):
#         pygame.draw.lines(screen, 'blue', False, test, 2) 
    # pygame.draw.line(screen, "blue",(746, 320), (746, 469)) #12
    # pygame.draw.line(screen, "blue",(746, 469), (395, 469)) #12
    # pygame.draw.line(screen, "blue", (395, 469), (395, 525)) #12
    # pygame.draw.line(screen, "blue",(395, 525), (130, 525)) #12
    # pygame.draw.line(screen, "blue", (130, 525), (130, 320)) #left
    # pygame.draw.line(screen, "blue",(130, 320),(746, 320)) #right
    # pygame.draw.line(screen, "blue",(577, 320),(577, 469)) #right

    wallpoints = [(766, 290), (766, 479), (415, 479), (415, 561), (110, 561), (110, 290),(766, 290)]
    for i in range(len(wallpoints)):
        pygame.draw.lines(screen, 'red', False, wallpoints, 2) 

    # pygame.draw.line(screen, "red",(766, 290), (766, 479)) #12
    # pygame.draw.line(screen, "red",(766, 479), (415, 479)) #12
    # pygame.draw.line(screen, "red", (415, 479), (415, 561)) #12
    # pygame.draw.line(screen, "red",(415, 561), (110, 561)) #12
    # pygame.draw.line(screen, "red", (110, 561), (110, 290)) #left
    # pygame.draw.line(screen, "red",(110, 290),(766, 290)) #right

    # pygame.draw.line(screen, "green",(130, 320),(746, 320)) #right
    # pygame.draw.line(screen, "green",(130, 320),(130, 525)) #right
    # pygame.draw.line(screen, "green",(130, 525),(746, 525)) #right
    # pygame.draw.line(screen, "green",(746, 320), (746, 525)) #right
    # test = [(215, 515), (230, 500), (245, 485), (260, 470), (320, 470), (335, 455), (740, 455)]
    # pygame.draw.lines(screen, 'green', False, test, 2) 

    for i in range(len(gen_route)):
        pygame.draw.lines(screen, 'green', False, gen_route[i], 2) 
    pygame.display.update()
pygame.quit()

