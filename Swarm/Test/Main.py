import Tello
import TelloUnity


def main():
    drone = Tello.Tello('', 8889)  
    vplayer = TelloUnity(drone)
    vplayer.root.mainloop() 


if __name__ == '__main__':
    main()