import moviepy.editor as mpy
from moviepy.video.io.bindings import mplfig_to_npimage
from moviepy.editor import clips_array
import numpy as np
import os
import matplotlib.pyplot as plt
import pandas as pd
import pickle

# This function was adapted from https://github.com/Tom-top/fiber_photometry_analysis
# The function generates a video that will align the behavior video, annotated behavior events and a signal.
# video_clip: video data loaded with moviepy. If False passed, the fucntion will only plot the behavior events and signal.
# x_data: numpy array with time space (second) data. Generally, this should be the Camera frame time space.
# behavior_df: Data frame with behavior events data. (behavior types x camera frame). 
# Column names will be used to identify behavior types. 
# Behavior events should be aligned to the camera frame time space, 1 when behavior is desplayed, 0 when not.
# signal_df: Data frame with signals to plot. (signals x camera frame). 
# Column names will be used to identify what the signal is.
# This can be used to plot multiple FP channels or multiple cells from miniscope imaging data.

def live_video_plot(video_clip, x_data, behavior_df,signal_df, **kwargs):


    # Extract behavior information from dataframe and process the dataframe to make it suitable for plotting
    behavior_df = behavior_df[behavior_df.columns[::-1]] #reverse data frame to make it easy to process
    behavior_names = behavior_df.columns
    behavior_step = kwargs["behavior_step"]
    for idx,key in enumerate(behavior_names):
        behavior_df[key] = behavior_df[key] + idx * behavior_step
    behavior_colors = kwargs["behavior_colors"]        
    behavior_array = np.array(behavior_df) # array that will be used for plotting
    
    # Extract signal information from dataframe and process the dataframe to make it suitable for plotting
    signal_df = signal_df[signal_df.columns[::-1]] #reverse data frame to make it easy to process
    signal_names = signal_df.columns
    signal_step = kwargs["signal_step"]
    for idx,key in enumerate(signal_names):
        signal_df[key] = signal_df[key] + idx * signal_step
    signal_array = np.array(signal_df) # array that will be used for plotting  
    signal_colors = kwargs["signal_colors"]
    #signal_colors.reverse()
    if signal_colors:
        signal_colors.reverse()
        if len(signal_colors) != len(signal_names):
            signal_colors = len(signal_names) * signal_colors # automatically update color to list of colors
    #print("signal_colors",signal_colors)
    #plt.plot(behavior_array)
    
    # The code is made to work in multiple behavior plots or single behavior plots.
    # KI wasn't able to figure out a way to plot both types with the same code.    
    if len(behavior_names) == 1:
        single_behavior_flag = True
    else:
        single_behavior_flag = False

    if len(signal_names) == 1:
        signal_single_flag = True
    else:
        signal_single_flag = False     

    # set display window    
    display_window = kwargs["display_window"] # in seconds

    # =============================================================================
    #     Function that will loop to create animation.
    # =============================================================================
    # for t (second), this will update the plot shown in the figure space.
    # To create a 3rd pannel with a second indicator, make anover live_ax1 for that purpose.
    def make_frame_mpl(t):
        
        #print('t ',t)

        # Web camera recording using TdT DAQ box generates inaccurate 
        # due to the Tdt system, the actual video fps and the camera fps is different
        # the adjustment variable will adjust this lag.
        if kwargs['TdT_framerate']:
            adjustment = kwargs["TdT_framerate"]/kwargs["video_framerate"]
            i = int(t*adjustment) 
        else:
            i = int(t) 
        #print(kwargs["display_window"]*kwargs["global_acceleration"])
        #print(i)
        #delta = (i/kwargs["global_acceleration"]) - kwargs["display_window"]
        #print((i/kwargs["global_acceleration"]))
        #live_ax0.set_xlim(x_data[0]+delta, x_data[0]+(i/kwargs["global_acceleration"])+ kwargs["display_window"])
        #live_ax1.set_xlim(x_data[0]+delta, x_data[0]+(i/kwargs["global_acceleration"])+ kwargs["display_window"])
        live_ax0.set_xlim(- display_window, display_window)
        live_ax1.set_xlim(- display_window, display_window)
        
        #try:
        for idx,plot in enumerate(behavior_plot):
            plot.set_data(x_data[0:i+kwargs["display_window"]*kwargs["video_framerate"]]-x_data[i],\
                    behavior_array[0:i+kwargs["display_window"]*kwargs["video_framerate"],idx,])
            if behavior_colors:
                print("behavior_colors",behavior_colors)
                plot.set_color(behavior_colors[idx])
        for idx,plot in enumerate(signal_plot):
            plot.set_data(x_data[0:i+kwargs["display_window"]*kwargs["video_framerate"]]-x_data[i],\
                    signal_array[0:i+kwargs["display_window"]*kwargs["video_framerate"],idx,]
                    )
            if signal_colors:
                plot.set_color(signal_colors[idx])
        #behavior_plot.set_data(x_data[0:i], behavior_array[0:i])
        #df_plot.set_data(x_data[0:i+kwargs["display_window"]*kwargs["global_acceleration"]]-x_data[i],\
        #    signal_df[0:i+kwargs["display_window"]*kwargs["global_acceleration"]])
        #except:
        #    print("Oups a problem occured")

        last_frame = mplfig_to_npimage(live_figure)
        return last_frame
    
    # =============================================================================
        #     Plotting functions
    # =============================================================================

    #number_subplots = len([x for x in y_data if len(x) != 0])
    number_subplots = 2 

    plt.style.use("dark_background")
    live_figure = plt.figure(figsize=(10, 6), facecolor='black')
    gs = live_figure.add_gridspec(nrows=number_subplots, ncols=1)
    
    # =============================================================================
    #     First live axis # This will plot the behavior events.
    # =============================================================================
    live_ax0 = live_figure.add_subplot(gs[0, :])
    
    #live_ax0.set_title("Behavior bouts : {0}".format(kwargs["behavior_to_segment"]), fontsize=10.)
    live_ax0.set_xlim(- display_window, display_window)
    #live_ax0.set_yticks([0, 1])
    #live_ax0.set_yticklabels(["Not behaving", "Behaving"], fontsize=10.)
    #live_ax0.set_ylim(-0.1, 1.1)
    
    
    #live_ax0.plot(behavior_df, '-',alpha = 0.8,ms = 1., lw=3.)
    if not single_behavior_flag:
        behavior_plot = live_ax0.plot(0,behavior_array[0,None],ls = '-', alpha=0.8, ms=1., lw=2.)
    else:
        behavior_plot = live_ax0.plot(0,behavior_array[0],ls = '-', alpha=0.8, ms=1., lw=2.)
    live_ax0.set_yticks(np.linspace(behavior_step/2,len(behavior_names)*behavior_step - behavior_step/2,len(behavior_names)))
    live_ax0.set_yticklabels(behavior_names)
    live_ax0.set_ylim(0-0.25,len(behavior_names)*behavior_step+0.25)
    live_ax0.axvline(0,ls =':',color= 'white')
    #live_ax0.set_xticks(np.linspace(step/2,len(behavior_names)*step - step/2,len(behavior_names)))
    #live_ax0.set_xticklabels(behavior_names)
    
    # =============================================================================
    #     Second live axis # This will plot the signal.
    # =============================================================================
    live_ax1 = live_figure.add_subplot(gs[1, :])
    
    live_ax1.set_title(r"$\Delta$F/F", fontsize=kwargs["fst"])
    live_ax1.set_xlim(- display_window, display_window)
    live_ax1.set_xlabel("Time (s)", fontsize=10.)
    #y_min, y_max, round_factor = utils.generate_yticks(signal_df, 0.1)
    
    ymin = kwargs['signal_ymin']
    ymax = kwargs['signal_ymax']
    ystep = kwargs['signal_ytick_step']
    ylabel = kwargs['signal_ylabel']
    
    if signal_single_flag:
        live_ax1.set_yticks(np.arange(ymin, ymax+ystep, ystep))
        live_ax1.set_yticklabels(np.arange(ymin, ymax+ystep, ystep,dtype = 'float16'), fontsize=10.)
        live_ax1.set_ylim(ymin, ymax)
        live_ax1.set_ylabel(ylabel)
        live_ax1.axvline(0,ls =':',color= 'white')
   
    else:
        live_ax1.set_yticks(0 + np.arange(len(signal_names))*signal_step)
        live_ax1.set_yticklabels(signal_names, fontsize=10.)
        live_ax1.set_ylim(-kwargs["signal_ylim_buffer"] , (len(signal_names))*signal_step+kwargs["signal_ylim_buffer"] )
        live_ax1.set_ylabel(ylabel)
        live_ax1.axvline(0,ls =':',color= 'white')

    #df_plot, = live_ax1.plot(0, signal_df[0], '-', color="green", alpha=1., ms=1., lw=3.)
    if not signal_single_flag:
        signal_plot = live_ax1.plot(0,signal_array[0,None],ls = '-', alpha=0.8, ms=1., lw=2.)
    else:
        signal_plot = live_ax1.plot(0,signal_array[0],ls = '-', alpha=0.8, ms=1., lw=2.,color = kwargs["signal_colors"][0])

    plt.tight_layout()


    # =============================================================================
    #     Create video and merge behavior videos with .
    # =============================================================================   


    animation = mpy.VideoClip(make_frame_mpl, duration=(kwargs["video_duration"] * kwargs["video_framerate"]))
    if video_clip:
        clips = [clip.margin(2, color=[0, 0, 0]) for clip in [(video_clip.resize(kwargs["resize_video"]).speedx(kwargs["global_acceleration"])),\
             animation.speedx(kwargs["global_acceleration"]).speedx(kwargs["video_framerate"])]]
        final_clip = clips_array([[clips[0]],
                             [clips[1]]],
                             bg_color=[0, 0, 0])
    else:
        clips = [clip.margin(1, color=[0, 0, 0]) for clip in [animation.speedx(kwargs["global_acceleration"]).speedx(kwargs["global_acceleration"])]]
        final_clip = clips_array([[clips[0]]],
                             bg_color=[0, 0, 0])
    
    if kwargs["buffer_window_key"]:
        final_clip = final_clip.subclip(t_start=kwargs["display_window"]/kwargs["global_acceleration"],\
             t_end=final_clip.duration-kwargs["display_window"]/kwargs["global_acceleration"])
    # final_clip.write_gif(os.path.join(kwargs["save_dir"],"Live_Video_Plot.gif"), fps=kwargs["live_plot_fps"])
    final_clip.write_videofile(os.path.join(kwargs["save_dir"],kwargs["video_name"] + ".mp4"), fps=kwargs["live_plot_fps"])

    plt.style.use("default")

    #return final_clip


def set_parameters(video_clip,x_data):
    if video_clip:
        video_duration = video_clip.duration  # Get metadata from the video file
        video_sampling_rate = int(video_clip.fps)
    else:
        video_duration = False # entry manually
        video_sampling_rate = 20
    kwargs = {}


    kwargs["display_window"] = 60 # The pre/post window to plot. # Seconds
    kwargs["video_duration"] = video_duration # Load the duration of the video. This will include the buffer window before and after the onset/offset of behavior of interest.
    kwargs["resize_video"] = 1.15 * (video_clip.size[1]*10/6)/video_clip.size[0] # Use this to resize the video size to plot size. The function will automatically correct the size.
    kwargs["video_framerate"] = video_sampling_rate
    kwargs["global_acceleration"] = 2 # How much to speed the plotting
    kwargs["fst"] = 12. #fontsize of titles in the plot
    
    kwargs["save_dir"] = '...'
    kwargs["video_name"] = 'Live_video'
    
    kwargs["live_plot_fps"] = video_sampling_rate 
    kwargs["buffer_window_key"] = True # If true the video will plot signals/behavior before and after the onset/offset. display_window will be used for the length of the window.
    kwargs["TdT_framerate"] = False # If you want to align a video which has inaccurate framerate, use this. Set this to the framerate specified in the DAQ.

    # Behavior plotting variables
    kwargs["behavior_step"] = 1.5 # Spacing between each line for behavior
    kwargs["behavior_colors"] = False # Color for behavior lines. If False, it will automatically color the events. 

    # Signal plotting variables
    kwargs['signal_ymin'] = -1 # Change this to set the ymin for the signal plotting. @MAKE THIS WORK AUTOMATICALLY
    kwargs['signal_ymax'] = 2 # Change this to set the ymax for the signal plotting.  @MAKE THIS WORK AUTOMATICALLY
    kwargs['signal_ytick_step'] = 0.25 # Change this to set the ystep for the yticks for signal plotting.  @MAKE THIS WORK AUTOMATICALLY
    kwargs['signal_ylabel'] = 'dF/F' # ylabel for signal
    kwargs['signal_step'] = 0.75 # Spacing between each line for signal 
    kwargs["signal_colors"] = ['green'] # Color for signal lines. If False, it will automatically color the events. If one color, all signals will be that color.
    kwargs["signal_ylim_buffer"] = 1 # Space above and below the first and last signal line.

    return kwargs
