import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
plt.rcParams['text.usetex'] = True

inte_range = np.array([-10,12])

#load file 
file_name = "RAW_data_20251226_151216.bin"
file = np.fromfile(file_name,dtype=np.uint8)# common decoding
file_head = np.fromfile(file_name,dtype=(np.void,4))# for finding general package head

idx_head = np.where(file_head==np.array([b'\x1E'b'\xAD'b'\xC0'b'\xDE'],dtype=(np.void,4)))*np.array([4])# index of head of package
idx_end = np.where(file_head==np.array([b'\x5A'b'\x5A'b'\x5A'b'\x5A'],dtype=(np.void,4)))*np.array([4])# index of end of package
print(f"{idx_head.shape[1]} package heading found")
print(f"{idx_end.shape[1]} package end found")

valid_length = np.min([idx_head.shape[1],idx_end.shape[1]])

# validation check
pack_info = np.unpackbits(np.stack((file[idx_head+np.array([6])].flatten(),file[idx_head+np.array([7])].flatten()),axis=1),axis=1)
P = pack_info[:,0]# even odd 1=> last 4bytes all 0; 0=> last 4bytes all data
E = pack_info[:,1]# pack error 1=> packaing error 0; 0=> no error
pack_length = pack_info[:,4:16]# package_length 12bit
convert_matr = np.logspace(11,0,num=12,base=2)# materix convert 12bit to int
pack_length_int = np.sum(pack_length*convert_matr,axis =1)# package_length int
length_check = np.equal(pack_length_int[0:valid_length]*8,(idx_end[:,0:valid_length]-idx_head[:,0:valid_length]+4))

if idx_head.shape[1] != idx_end.shape[1]: print("Warning: dismatch between number of package headings and package ends, ignore the last heading")
idx_head = idx_head[:,0:valid_length]
idx_end = idx_end[:,0:valid_length]
#print(idx_head.shape)
#print(idx_end.shape)


print(f"Packing check: {E}")
print(f"Found pack at {np.where(E.astype(bool))[0]} with error, total {np.count_nonzero(np.logical_not(E.astype(bool)))} packages pass packing check")
print(f"Length check: {length_check}")
print(f"Found pack at {np.where(np.logical_not(length_check))[1]} with error, total {np.count_nonzero(length_check)} packages pass length check")
# unpack package detail
board_id = file[idx_head+np.array([9])]
pack_id = file[idx_head+np.array([10])]
#print(pack_id)
#print(board_id)

existed_board_id = np.unique(board_id)
print(f"Board with ID {existed_board_id} founded in the file")
existed_pack_id = np.unique(pack_id)
print(f"Package with ID {existed_pack_id} founded in the file")

existed_board_id_new = np.zeros(existed_board_id.shape[0])
for idx,new_id in enumerate(np.array([254,18,16,19,2,5,17,15,28,13])):
    existed_board_id_new[existed_board_id == new_id] = idx
print(f"New id applied {existed_board_id_new}({existed_board_id_new.shape[0]})")

print("Relation ship between old and new ids")
for idx in range(existed_board_id_new.shape[0]):
    print(f"{existed_board_id[idx]} -> {existed_board_id_new[idx]}")

# find maxima repeat number of package ids
pack_id_repeat = np.zeros([existed_board_id.shape[0],existed_pack_id.shape[0]])
for idx_baord_id in range(0,existed_board_id.shape[0]):
    address =  np.where(board_id == existed_board_id[idx_baord_id])
    for idx_pack_id in range(0,existed_pack_id.shape[0]):
        repeated_id = np.where(pack_id[address] == existed_pack_id[idx_pack_id])
        pack_id_repeat[idx_baord_id,idx_pack_id] = len(repeated_id[0])
        
pack_id_count = int(np.max(pack_id_repeat))
print(f"Maxima {pack_id_count} repeats of pack id found")


genral_pack_pointer = np.zeros([existed_board_id.shape[0],existed_pack_id.shape[0],pack_id_count])
# Pointer pointing idx_head, idx_head[genral_pack_pointer[i,j,k]] means address of package with board id i and package id j and k-th repeat in file  
genral_pack_pointer_valid = np.zeros([existed_board_id.shape[0],existed_pack_id.shape[0],pack_id_count],dtype=bool)

# Find pointer value
for idx_baord_id in range(0,existed_board_id.shape[0]):
    #print(existed_board_id[idx_baord_id])
    address =  np.where(board_id == existed_board_id[idx_baord_id])
    for idx_pack_id in range(0,existed_pack_id.shape[0]):
        pack_address = np.where(pack_id[0,address[1]] == existed_pack_id[idx_pack_id])
        genral_pack_pointer[idx_baord_id,idx_pack_id,0:len(pack_address[0])] = address[1][pack_address[0][0:len(pack_address[0])]]
        genral_pack_pointer_valid[idx_baord_id,idx_pack_id,0:len(pack_address[0])] = True

genral_pack_pointer = genral_pack_pointer.astype(np.int32)
#print(genral_pack_pointer)
#print(genral_pack_pointer_valid)
#test code
"""
#test board id validation
print(existed_board_id)
test_id = idx_head[0,genral_pack_pointer[9,0,0][genral_pack_pointer_valid[9,0,0]]][0]
print(test_id)
print(file[test_id:test_id+20])

#test valid function validation
print(genral_pack_pointer[1,0,:][genral_pack_pointer_valid[1,0,:]])
"""

# ! imnportant as external trigger pack would only be the first 1to 3 packs. no specicic procress is taken here.
sub_pack_head = np.unpackbits(file[idx_head+np.array([12])].T,axis=1)
# package type
sub_pack_type = sub_pack_head[:,0:2]
if_data_package = np.logical_and(np.equal(sub_pack_type,np.array([1,0]))[:,0],np.equal(sub_pack_type,np.array([1,0]))[:,1])# true if the package is a data package else a trigger package
print(f"Package at {np.where(np.logical_not(if_data_package))[0]} are external trigger package ({np.where(np.logical_not(if_data_package))[0].shape[0]} packages)")
# channel number
sub_pack_channel_id = sub_pack_head[:,2:8]
convert_matr2 = np.logspace(5,0,num=6,base=2)# materix convert 6bit to int
sub_pack_channel_id_int = np.sum(sub_pack_channel_id * convert_matr2,axis=1).astype(np.int32)

sub_pack_length = file[idx_head+np.array([13])]*np.array([16])
sub_pack_id = file[idx_head+np.array([14])]*np.array([256])+file[idx_head+np.array([15])]

# trigger souce
convert_matr3 = np.logspace(2,0,num=3,base=2)# materix convert 3bit to int
sub_pack_trigger_source = np.sum(np.unpackbits(file[idx_head+np.array([19])].T,axis=1)[:,5:8] * convert_matr3,axis=1).astype(np.int32)

# trigger souce count
sub_pack_trigger_source_count = (file[idx_head+np.array([20])]*np.array([256])+file[idx_head+np.array([21])])[0][if_data_package]
#print(sub_pack_trigger_source_count)
print(f"Trigger source count of {np.unique(sub_pack_trigger_source_count)} found")

# trigger souce time stamp
convert_matr4 = np.logspace(4*5,0,num=6,base=2)# materix convert 6byte to int
#print(convert_matr4)
sub_pack_trigger_source_stamp = np.sum(np.array([
                                          file[idx_head+np.array([22])][0],
                                          file[idx_head+np.array([23])][0],
                                          file[idx_head+np.array([24])][0],
                                          file[idx_head+np.array([25])][0],
                                          file[idx_head+np.array([26])][0],
                                          file[idx_head+np.array([27])][0]]).T*convert_matr4,axis=1).astype(np.int64)
#sub_pack_trigger_source_stamp = np.array([hex(stamp) for stamp in sub_pack_trigger_source_stamp])
#print(sub_pack_trigger_source_stamp.T)
#print(sub_pack_trigger_source_stamp.shape)

wave_sample_data = np.zeros([idx_end.shape[1],np.max(sub_pack_length)]) 
wave_sample_data_valid = np.zeros([idx_end.shape[1],np.max(sub_pack_length)],dtype=bool) 
#print(wave_sample_data.shape)
for idx_sub_pack in range(idx_head.shape[1]):
    if not if_data_package[idx_sub_pack] : continue
    this_sub_pack_length = sub_pack_length[:,idx_sub_pack][0]*2
    if P[idx_sub_pack].astype(bool): this_data = file[idx_head[:,idx_sub_pack][0]+28:idx_head[:,idx_sub_pack][0]+24+this_sub_pack_length]
    else: this_data = file[idx_head[:,idx_sub_pack][0]+28:idx_head[:,idx_sub_pack][0]+28+this_sub_pack_length]
    this_data_front = this_data[::2]
    this_data_rear = this_data[1::2]
    wave_sample_data[idx_sub_pack,0:int(this_sub_pack_length/2)] = this_data_front*np.array([256])+this_data_rear
    wave_sample_data_valid[idx_sub_pack,0:int(this_sub_pack_length/2)] = True

#print(wave_sample_data)

#test code
"""
idx = genral_pack_pointer[1,1,0][genral_pack_pointer_valid[1,1,0]]
plt.plot(wave_sample_data[idx][wave_sample_data_valid[idx]])
plt.xlabel("Time")
plt.ylabel("Data")
plt.title(f"Board id: {board_id[0,idx][0]},channel id: {sub_pack_channel_id_int[idx][0]},time stamp: {sub_pack_trigger_source_stamp[idx[0]]}")
plt.savefig("output")
"""

#now use board id, channel id and time stamp to label a package
existed_channel_id = np.unique(sub_pack_channel_id_int)
existed_time_stamp = np.unique(sub_pack_trigger_source_stamp)
print(f"Channel id of {existed_channel_id} found")
print(f"Time stamp of {existed_time_stamp} found, ({existed_time_stamp.shape[0]} time stamps)")

#this pointer uses board id, channel if and time stamp to label a package
pack_pointer_board_channel_timeStamp = np.zeros([existed_board_id.shape[0],existed_channel_id.shape[0],existed_time_stamp.shape[0]],dtype=np.int32)
pack_pointer_board_channel_timeStamp_valid = np.zeros([existed_board_id.shape[0],existed_channel_id.shape[0],existed_time_stamp.shape[0]],dtype=bool)
#as we do not expect more than 3 external trigger pack found 
ext_tri = np.zeros(np.where(np.logical_not(if_data_package))[0].shape[0]).astype(np.int32)
num_ext_tri = 0

for idx_board in range(existed_board_id.shape[0]):
    for idx_pack in range(existed_pack_id.shape[0]):
        for idx_repeat in range(genral_pack_pointer.shape[2]):
            #print(f"{idx_board},{idx_pack},{idx_repeat}")
            if not genral_pack_pointer_valid[idx_board,idx_pack,idx_repeat]: continue
            file_pointer = genral_pack_pointer[idx_board,idx_pack,idx_repeat]
            if not length_check[0,file_pointer]: continue
            if P[file_pointer].astype(bool): continue
            if not if_data_package[file_pointer]: 
                ext_tri[num_ext_tri] = file_pointer
                num_ext_tri += 1
                continue
            #print(file_pointer)
            this_channel = sub_pack_channel_id_int[file_pointer]
            this_timeStamp = sub_pack_trigger_source_stamp[file_pointer]
            #print(np.where(existed_channel_id==this_channel)[0])
            #print(np.where(existed_time_stamp==this_timeStamp)[0])
            pack_pointer_board_channel_timeStamp[idx_board,
                                                np.where(existed_channel_id==this_channel)[0].astype(np.int32),
                                                np.where(existed_time_stamp==this_timeStamp)[0].astype(np.int32)
                                                ] = file_pointer
            pack_pointer_board_channel_timeStamp_valid[idx_board,
                                                       np.where(existed_channel_id==this_channel)[0].astype(np.int32),
                                                       np.where(existed_time_stamp==this_timeStamp)[0].astype(np.int32)
                                                       ] = True

print(f"Number of valid data package pointer: {np.count_nonzero(pack_pointer_board_channel_timeStamp_valid)}")

# process ext tri pack(if found)
if num_ext_tri != 0:
    print(f"{num_ext_tri} external trigger package found")
    for idx_tri in range(num_ext_tri):
        #print(f"Raw package{file[idx_head[0,ext_tri[idx_tri]]:idx_head[0,ext_tri[idx_tri]]+32]}")
        #print(ext_tri[idx_tri])
        exceed = np.unpackbits(file[idx_head[0,ext_tri[idx_tri]]+13])[-1]
        ext_tri_count = file[idx_head[0,ext_tri[idx_tri]]+14]*256 + file[idx_head[0,ext_tri[idx_tri]]+15]
        ext_tri_stamp_exceed = np.unpackbits(file[idx_head[0,ext_tri[idx_tri]]+21])[-1]
        ext_tri_source_stamp = sub_pack_trigger_source_stamp[ext_tri[idx_tri]]
        #print(f"External trigger {idx_tri+1}. Trigger count: {ext_tri_count} (exceed:{exceed}),Trigger time stamp: {ext_tri_source_stamp}(exceed:{ext_tri_stamp_exceed})")
else: print("No external trigger package found")
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

"""
#print(sub_pack_trigger_source_stamp)
board_id_idx_test = np.where(existed_board_id==254)[0]
idx = pack_pointer_board_channel_timeStamp[board_id_idx_test][pack_pointer_board_channel_timeStamp_valid[board_id_idx_test]]
print(idx)
print(sub_pack_trigger_source_stamp[idx])
print(sub_pack_trigger_source_count[idx])
"""

idx_g_board = []
idx_g_channel = []
idx_g_timestamp = []
for idx_board_tri in range(existed_board_id.shape[0]):
    for idx_channel_tri in range(existed_channel_id.shape[0]):
        for idx_timestamp_tri in range(existed_time_stamp.shape[0]):
            if not pack_pointer_board_channel_timeStamp_valid[idx_board_tri,idx_channel_tri,idx_timestamp_tri]: continue
            idx = pack_pointer_board_channel_timeStamp[idx_board_tri,idx_channel_tri,idx_timestamp_tri]
            if not existed_board_id[idx_board_tri] == 19: continue
            if not existed_channel_id[idx_channel_tri] == 32: continue
            if np.max(wave_sample_data[idx][wave_sample_data_valid[idx]]) >= 500:
                idx_g_board.append(idx_board_tri)
                idx_g_channel.append(idx_channel_tri)
                idx_g_timestamp.append(idx_timestamp_tri)
idx_g_board = np.array(idx_g_board).astype(np.int32)
idx_g_channel = np.array(idx_g_channel).astype(np.int32)
idx_g_timestamp = np.array(idx_g_timestamp).astype(np.int32)
print(f"{idx_g_board.shape[0]} package labeled")
#print(np.unique(existed_board_id[idx_g_500_board]))
#print(idx_g_500_board)
plt.figure()
plt.hist(existed_board_id_new[idx_g_board],bins = 4,range=(0,4))
plt.ylabel(r"$Count$")
plt.xlabel(r"$Board ID$")
plt.savefig("Hist_board")

plt.figure()
plt.hist(existed_channel_id[idx_g_channel],bins = 64,range=(0,63))
plt.ylabel(r"$Count$")
plt.xlabel(r"$Channel ID$")
plt.savefig("Hist_channel")

#"""
for idx in tqdm(range(idx_g_board.shape[0])):
    board_id_idx_test = idx_g_board[idx]#0#np.where(existed_board_id==2)[0]
    channel_id_idx_test = idx_g_channel[idx]#0#np.where(existed_channel_id==47)[0]
    #print(np.where(pack_pointer_board_channel_timeStamp_valid[board_id_idx_test,channel_id_idx_test,:]))
    timeStamp_idx_test = idx_g_timestamp[idx]#np.where(pack_pointer_board_channel_timeStamp_valid[0,0,:])[0][0]#np.where(existed_time_stamp=='0xf8d5610')[0]
    #print(timeStamp_idx_test)

    board_id_test = existed_board_id[board_id_idx_test]
    channel_id_test = existed_channel_id[channel_id_idx_test]
    timeStamp_test = existed_time_stamp[timeStamp_idx_test]

    #print(f"Test board id: {board_id_test},test channel_id: {channel_id_test}, test timeStamp: {timeStamp_test}")

    if pack_pointer_board_channel_timeStamp_valid[board_id_idx_test,channel_id_idx_test,timeStamp_idx_test]:
        #print("Pack found")
        idx = pack_pointer_board_channel_timeStamp[board_id_idx_test,channel_id_idx_test,timeStamp_idx_test]
        output_data = wave_sample_data[idx][wave_sample_data_valid[idx]]

        #found maxima
        if np.max(output_data) == 4095:
            idx_max = np.round(np.mean(np.where(output_data==4095)[0])).astype(np.int32)
        else: idx_max = np.argmax(output_data)
        area = np.trapz(output_data[idx_max+inte_range[0]:idx_max+inte_range[1]],dx = 25)# unit of dx = ns
        output_mean = np.mean(output_data)
        output_std = np.std(output_data)
        plt.figure()
        #plt.text(300,10,rf'$\sigma = {output_std:.3f},\\ mean = {output_mean:.3f}$')
        plt.plot(output_data)
        plt.annotate(text = rf'$Area: {area:.1f} \enspace LSB \times ns \\ Index \enspace of \enspace Maxima: {idx_max}$',xy=(idx_max+inte_range[1]+1,np.max(output_data)*0.9))
        plt.fill_between(np.arange(idx_max+inte_range[0],idx_max+inte_range[1]+1),output_data[idx_max+inte_range[0]:idx_max+inte_range[1]+1],color = "c",hatch='//',alpha=0.3)
        plt.axvline(idx_max+inte_range[0],ls='--',color = 'r')
        plt.axvline(idx_max+inte_range[1],ls='--',color = 'r')
        plt.xlabel(r'$Time (\times 25ns)$')
        plt.ylabel(r'$Data$')
        plt.ylim(bottom=0)
        plt.title(rf'$Board Id: {board_id[0,idx]}(New Id:{existed_board_id_new[existed_board_id == board_id[0,idx]].astype(np.int32)[0]}),Channel Id: {sub_pack_channel_id_int[idx]},Time Stamp: {sub_pack_trigger_source_stamp[idx]}$')
        plt.savefig(f"output/B{board_id_test}C{channel_id_test}T{timeStamp_test}.png")
        plt.close()
        idx_head_test = idx_head[0,idx]
        #print(file[idx_head_test:idx_head_test+800])

    else: print("Pack not found")
#"""
"""
# statistical anaylsis, This is used to found out different bg noice accross different channel and different board
for idx_board_sta in range(existed_board_id.shape[0]):
    channel_noise_mean = np.zeros([existed_channel_id.shape[0]])
    channel_noise_sigma = np.zeros([existed_channel_id.shape[0]])
    channel_noise_size = np.zeros([existed_channel_id.shape[0]])
    for idx_channel_sta in range(existed_channel_id.shape[0]):
        idx = pack_pointer_board_channel_timeStamp[idx_board_sta,idx_channel_sta,pack_pointer_board_channel_timeStamp_valid[idx_board_sta,idx_channel_sta,:]]
        channel_noise_size[idx_channel_sta] = wave_sample_data[idx].shape[0]
        if np.logical_not(channel_noise_size[idx_channel_sta]==0):
            channel_noise_mean[idx_channel_sta] = np.mean(wave_sample_data[idx])
            channel_noise_sigma[idx_channel_sta] = np.std(wave_sample_data[idx])
        else:
            channel_noise_mean[idx_channel_sta] = np.nan
            channel_noise_sigma[idx_channel_sta] = np.nan
    fig,ax1 = plt.subplots(2,1,sharex=True)
    ax1[0].plot(channel_noise_mean,label = r'$\overline{noise}$',color='b')
    ax2 = ax1[0].twinx()
    ax2.plot(channel_noise_sigma,label = r'$\sigma$',color='r')
    fig.legend()
    
    ax1[0].set_ylabel(r'$Data$')
    ax1[0].set_title(rf'$Board \enspace ID \enspace {board_id[0,idx][0]}$')
    
    ax1[1].step(existed_channel_id,channel_noise_size,where = 'mid')
    ax1[1].set_ylabel(r'$Package \enspace count$')
    ax1[1].set_xlabel(r'$Channel \enspace ID$')
    for idx_channel_sta in range(existed_channel_id.shape[0]):
        if channel_noise_size[idx_channel_sta] == 0:
            if idx_channel_sta < existed_channel_id.shape[0]/2:
                ax1[1].annotate(text = rf'$Suspected \enspace error \enspace \\ at \enspace channel \enspace id \enspace{existed_channel_id[idx_channel_sta]}$',
                            xy = (existed_channel_id[idx_channel_sta],0),
                            xytext = (existed_channel_id[idx_channel_sta]+5,150),
                            size = 10,
                            arrowprops=dict(arrowstyle="->", connectionstyle="arc3",linestyle = '--'),
                            )
            else:
                ax1[1].annotate(text = rf'$Suspected \enspace error \enspace \\ at \enspace channel \enspace id \enspace{existed_channel_id[idx_channel_sta]}$',
                            xy = (existed_channel_id[idx_channel_sta],0),
                            xytext = (existed_channel_id[idx_channel_sta]-25,150),
                            size = 10,
                            arrowprops=dict(arrowstyle="->", connectionstyle="arc3",linestyle = '--'),
                            )
    fig.savefig(f"noise_boardID{board_id[0,idx][0]}")
"""