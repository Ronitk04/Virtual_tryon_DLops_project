from test import test1, test2, transf,remo
import streamlit as st
import PIL.Image as Image
import os
import random

def app():
    st.title('Virtual Try-On')
    st.write('Upload an image of yourself and try on different clothes!')

    # Add a file selector for the user's folder
    # folder_path = st.text_input('Enter folder path', value='D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data/train/cloth')
    # if not os.path.exists(folder_path):
    #     st.error('Folder path does not exist')
    #     return

    # # Get a list of all image files in the folder
    # image_files = [os.path.join(folder_path, file_name) for file_name in os.listdir(folder_path) if file_name.endswith(('jpg', 'jpeg', 'png'))]

    # if len(image_files) == 0:
    #     st.warning('No image files found in folder')
    #     return

    # # Display the images in a grid layout
    # for i, image_file in enumerate(image_files):
    #     image = Image.open(image_file)
    #     resized_image = image.resize((256, 192))
    #     st.image(resized_image, caption=image_file, use_column_width=True)
    #     if st.checkbox('Save this image',key=random.randint(1,2000)):
    #         # Save a text file with the image filename
    #         # filename = resized_image.name.split('.')[0] + '.txt'
    #         with open("D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data/train/cloth/"+resized_image.name.split('.')[0]+".txt", 'w') as f:
    #             f.write('This is a text file for ' + resized_image.name)
    #     # st.write(f'Checkpoint {i+1} - {image_file}')
        # Get the list of image files in the folder
    image_folder = 'D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data/train/cloth/'
    image_files = [os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith('.jpg') or f.endswith('.png')]
    image_person = "000008_0.jpg"
    person_path = "D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data/train/image/000008_0.jpg"
    image_per = Image.open(person_path)
    st.image(image_per,caption="Person to try on")
    # Display the images in a grid layout
    for i, image_file in enumerate(image_files):
        image = Image.open(image_file)
        resized_image = image
        st.image(resized_image, caption=image_file, use_column_width=False,)
        if st.checkbox('Save this image', key=i):
            # Save a text file with the image filename
            filename = os.path.splitext(os.path.basename(image_file))[0] + '.txt'
            with open(os.path.join("D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data/train/", "train_pairs.txt"), 'w') as f:
                f.write(image_person+" "+os.path.basename(image_file))
                st.write(f'Text file generated for {image_file}: {filename}')
    test1()
    remo()
    transf()
    test2()
    image_person_changed = "000008_0.jpg"
    # D:\IIT Jodhpr\3rd year\2nd sem\deep learning\DL_ops project\Deploy\data\TOM\train\try-on\000008_0.jpg
    person_path = "D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data/TOM/train/try-on/000008_0.jpg"
    image_per = Image.open(person_path)
    st.write("person with applied cloth try-on")
    st.image(image_per,caption="final_path")
if __name__ == '__main__':
    app()