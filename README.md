# bee_system
The full system to run on the flight raspberry pi

# Install Instructions
1. Download the aravis library:

    cd ~
    git clone https://github.com/AravisProject/aravis.git
    
2. Download this tool

   pip install git+https://github.com/lionfish0/bee_system.git

3. Add the relevant paths to make aravis work:

   export GI_TYPELIB_PATH=$GI_TYPELIB_PATH:~/aravis/src
   export LD_LIBRARY_PATH=~aravis/src/.libs
  
