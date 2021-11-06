import cv2
import numpy as np
import matplotlib.pyplot as plt
import picamera
import os
from imutils import grab_contours

#------------------------------Camera Class-----------------------------------

# Consists of setters and getters for camera settings
# Capture takes a picture and saves it to a directory 

class Camera():
    def __init__(self):
        self.cam = picamera.PiCamera()
        self.cam.resolution = (1920, 1080)
        self.cam.exposure_mode = 'off'
        self.cam.framerate = 10
        self.cam.shutter_speed = 0
        self.cam.iso = 0
        self.cam.start_preview()
    
    def get_framerate(self):
        return self.cam.framerate
    
    def get_analog_gain(self):
        return self.cam.analog_gain
        
    def get_digital_gain(self):
        return self.cam.digital_gain
        
    def get_shutter_speed(self):
        return self.cam.shutter_speed
    
    def get_iso(self):
        return self.cam.iso
        
        
    def set_framerate(self, rate):
        self.cam.framerate = rate
    
    def set_iso(self, iso):
        self.cam.iso = iso
        
    def set_shutter_speed(self, speed):
        self.cam.shutter_speed = speed
        
        
    def capture(self, directory):
        self.cam.capture(directory)
        #self.cam.stop_preview()
        
    def close(self):
        self.cam.close()
        
        
#----------------------Initialize Variables------------------------------------
    
# global variables
angles = []
intensities = []

# initialize cam object
cam = Camera()

#cam.set_framerate(20)
#cam.set_shutter_speed(1000)
#cam.set_iso(2)


#print("framerate: ", cam.get_framerate())
#print("anagalog: ", cam.get_analog_gain())
#print("digital: ", cam.get_digital_gain())
#print("shutter speed: ", cam.get_shutter_speed())
#print("iso: ", cam.get_iso())

def show_img(img):
    cv2.imshow("img", img)
    cv2.waitKey(0) 
    cv2.destroyAllWindows()


#------------------------Main Functions----------------------------------------
'''

Capture() - Captures an image and returns light intensity if image is not saturated
    *OVERWRITES PREVIOUS SAVED IMAGE OF NAME "IMG" WITH EACH FUNCTION CALL*

Capture(angle, boolean=False) - Captures an image and saves it with angle as name,
    if boolean == True: shows the plot of intensity Vs Angle
    if boolean == False: returns calculated intensity at angle

    *if second argument is not passed, it is automatically set to false*

Reset() - Clears all data points on the scatter plot in order to plot new angle range

plot_folder_images(folder) - Calculates  and plots the intensity of images in a folder

export_plot(name) - Exports the scatter plot as a png to the same directory as this python file.
'''


#--------------------Saturation Calculations-----------------------------------


# Determines percentage of saturated pixels
# If the number of saturated pixels makes up 95% of the image, 
# not including the background, then the image is saturated   
# Returns a boolean, True, if image is saturated. Otherwise, return False
def percent_saturated(img_bgr):
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1];
    saturated_pixels = np.count_nonzero(saturation == 255)
    zeros = np.count_nonzero(saturation == 0)
    total_pixels = saturation.size
    
    # Can change 0.95 (95%) threshold 
    return saturated_pixels != 0 and saturated_pixels / (total_pixels - zeros) > 0.95



# Counts the number of saturated pixel clusters in the a grayscale image.
# Converts all values less than 255 to 0 by thresholding.
# Performs a series of dilation and erosion to remove small noise on the image.
# Draw a contour around the cluster of saturated pixels from the threshold image.
# Returns a tuple of the number of circles (groups of saturated pixels) and the radius of each circle.
def group_saturated(img_gray):
    ret, thresh = cv2.threshold(img_gray.copy(), 254, 255, cv2.THRESH_TOZERO)
    thresh = cv2.erode(thresh, None, iterations=2)
    thresh = cv2.dilate(thresh, None, iterations=4)
    

    # Draw contour  
    # RETR_EXTERNAL: return only extreme outer flags and leave child contours behind 
    #   Outer contours only
    # CHAIN_APPROX_SIMPLE: compresses horizontal, vertical, and diagonal segments
    #   Leaves only their end points
    #  Contours is a Python list of all the contours in the image. 
    # Each individual contour is a Numpy array of (x,y) coordinates of boundary points of the object.
    contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = grab_contours(contours)
 
    count = 0
    rad = []
   
    for i, cnt in enumerate(contours):
        # It is a circle which completely covers the object with minimum area.
        # returns the center of the circle and the radius
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        
        # img, center coordinates, radius, colour of the border line, thickness
        cv2.circle(img_gray, (int(x), int(y)), int(radius),
    		(0, 0, 255), 3)
   
        count = i+1
        rad.append(radius)
    
    show_img(img_gray)

    return count, rad

# Determines saturated image by counting the clusters of saturated pixels and its radius
# If there is a group of 255 pixels detected and the radius of that is greater than 20
# then it is a saturated image
# Returns a boolean, True, if image is saturated. Otherwise, return False
def is_saturated2(img_gray):
    bgr = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
    count, radius = group_saturated(img_gray)
    return count > 0 and max(radius) > 90 and percent_saturated(bgr)



#------------------------------Intensity Calculations--------------------------

# Calculates intensity by summing all pixel values in grayscale
def sum_intensity(img_bgr):
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).sum()


#Calculate light intensity using HLS image format
def light_HLS(img):
    light = img[:,:,1]
    total_light = np.sum(light)
    pixels = img.shape[0] * img.shape[1]
    black_p = np.count_nonzero(light == 0)
    Avg_light = total_light / (pixels - black_p)

    return Avg_light


#--------------------------------Plotting--------------------------------------

# Shows a plot of x (list of angles) and y (list of intensities) connected through dashes
def plot_dash(x, y):
    plt.title("Intensity vs Angle")
    plt.xlabel("Angle (°)")
    plt.ylabel("Intensity")
    plt.plot(x, y, linestyle='--', dashes=(5, 1))
    plt.show()
    
# Shows a scatter plot of x (list of angles) and y (list of intensities)
def plot_scatter(x, y):
    plt.title("Intensity vs Angle")
    plt.xlabel("Angle (°)")
    plt.ylabel("Intensity")
    plt.scatter(x, y)
    plt.show()

        
# Calculates the intensity of images in a folder
# folder location is in same directory as this code file
# Plots the calculated intensity
# check img types --> bgr/gray/hls
def plot_folder_images(folder_name):
    cur_path = os.path.dirname(os.path.realpath(__file__))
    # Change folder name
    img_path = os.path.join(cur_path, folder_name)
    
    intensity_list = []
    angle_list = []

    for i, img in enumerate(os.listdir(img_path)):
        path = os.path.join(img_path, img)
        
        gray = cv2.imread(path, 0)
       
        # check if image is saturated
        if not is_saturated2(gray):
            # convert image to HLS
            bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            hls = cv2.cvtColor(bgr, cv2.COLOR_BGR2HLS)
            intensity_list.append(light_HLS(hls))
           
            angle = []
            
            for letter in img:
                if letter.isdigit():
                    angle.append(letter)
           
            angle = "".join(angle)
            angle_list.append(int(angle))
            
        else:
            print(img + " is saturated")
        
    
    # plot the function
    plot_scatter(angle_list, intensity_list)
    

#Exports the scatter plot as a png
def export_plot(name):
    plt.savefig(name+'.png',format='png')

     
#Clear matplotlib graph in order to plot new angle range
def reset():
    # reinitialize global variables
    del angles[:]
    del intensities[:]
    cam.close()
    

#--------------------------Extras---------------------------------------------
# img: image to add text
# text: String to write on image at location x,y
def add_text(img, text, x, y):
    location = (x,y)
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = .7
    fontColor = (255, 0, 0)
    lineType = 2
    cv2.putText(img, text, 
                location, 
                font,
                fontScale,
                fontColor,
                lineType)
    return img

    
    
#--------------------------------Capture--------------------------------------

#Captures FHD image and returns light intensity
#OVERWRITES PREVIOUS SAVED IMAGE OF NAME "IMG"!
def capture():
    directory = "/home/pi/Desktop/Image_Acquisition/test_img/img.png"
    cam.capture(directory)
    gray = cv2.imread(directory + '/img.png',0)
    
    #Checks if image is saturated
    if is_saturated2(gray) and gray.dtype == 'uint8':
        print("ERROR: Image is Saturated")
        return 0;

    bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    #Can adjust threshold cut off value
    th, dst = cv2.threshold(bgr,0,255,cv2.THRESH_TOZERO)
    #BGR -> HLS
    imgHLS = cv2.cvtColor(dst, cv2.COLOR_BGR2HLS)
    
    return light_HLS(imgHLS)



# Captures image (with angle as name)
# If boolean == True: shows the plot of image
# If second argument is not passed, it is automatically set to False
# If boolean == False: returns calculated intensity at angle
def capture(angle,boolean=False):

    directory = '/home/pi/Desktop/Image_Acquisition/test_img/'
    cam.capture(directory + angle + '.png')
    gray = cv2.imread(directory + angle +'.png',0)

    if is_saturated2(gray) and gray.dtype == 'uint8':
        print("ERROR: Image is Saturated")
        gray_text = add_text(gray, "SATURATED", 10, 90)
        return 0;
    
    # Add text to image
    gray_text = add_text(gray, directory, 10, 30)
    gray_text = add_text(gray, "Angle: " + angle, 10, 60)
    print("Angle: ", angle)
    
    cv2.imwrite('/home/pi/Desktop/Image_Acquisition/text_img/' + angle + '.png', gray_text) 
    

    bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    #Can adjust threshold cut off value
    th, dst = cv2.threshold(bgr,0,255,cv2.THRESH_TOZERO)
    imgHLS = cv2.cvtColor(dst, cv2.COLOR_BGR2HLS)

    # calculate the intensity
    intensity = light_HLS(imgHLS)
    
    # append calculated values to list
    intensities.append(intensity)
    angles.append(angle)
    
    # Plot points
    if boolean:
        plot_scatter(angles, intensities)
        plot_dash(angles,intensities)
    
    return intensity

    
def main():
    
    directory = '/home/pi/Desktop/Image_Acquisition/sample_laser/45.jpg'
    gray = cv2.imread(directory, cv2.IMREAD_GRAYSCALE)
    
    print("test capture:")
    #for angle in range(90,95):
    #    capture(str(angle))
    #capture('95', True)
    
    print("Show group saturated images")
    #show_img(gray)
    #group_saturated(gray)
    
    print("sample laser images plot:")
    plot_folder_images("sample_laser")
    print('test img images plot:')
    plot_folder_images("test_img")

main()
