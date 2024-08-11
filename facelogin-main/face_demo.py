import face_recognition
import cv2
import sys

def main(image_path):
    # Lade das Bild und erkenne Gesichter
    image = face_recognition.load_image_file(image_path)
    face_landmarks_list = face_recognition.face_landmarks(image)

    # Konvertiere das Bild in ein OpenCV-Format
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Zeichne die Gesichtsmerkmale für jedes Gesicht
    for face_landmarks in face_landmarks_list:
        for facial_feature in face_landmarks.keys():
            points = face_landmarks[facial_feature]
            for point in points:
                cv2.circle(image, point, 2, (0, 0, 255), -1)

    # Zeige das Bild an
    cv2.imshow('Facial Features', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python facial_features_demo.py path/to/image.jpg")
    else:
        main(sys.argv[1])