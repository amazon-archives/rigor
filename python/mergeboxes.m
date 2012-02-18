% This programs merge all (rectangular) bounding boxes coming from our test detector applied to
% any image. It was tested with 640x480 and 320x240 images
%%%%%%%%%%
%%NOTE: We are using 1/8 as a scaling factor that actually exists as a paramter in the TD but since we are not passing the TD objects here, we are hardcoding it much to Kaolin's and my displeasure!

function mergeboxes(rect_info,im) 
% For some specific parameters of the text detector we have 6 layers with dimensions:
%disp(rect_info)
smallimage = 0;		% To choose size of image 1 for 320x240, 0 for 640x480
if nargin < 2
	savingimages = 0;	% To save intermediate images (1/0)
end
%The rigor/python code gives us values of coordinates of boxes starting top left but this code uses the system of top,left,bottom,right
top = rect_info(:,3); %Y vals from the first coord
left = rect_info(:,2); %X vals from the first coord
bottom = rect_info(:,7); % Y val from the third coord
right = rect_info(:,6); % X val from the third cord
layer = rect_info(:,1);
weights = rect_info(:,10);

clear rect_info;



% These values are the dimension for boxes from every layer. It depends on the number of layers from the text
% detector. These are for 6 and 9 layers only.
%if smallimage
	%% Dimensions of boxes for every layer. Actually it is this plus one but this is what matters for us.
	%% Format: [height_box width_box] per row
	%boxdim = [48 88; 68 112; 84 144; 24 44; 34 56; 42 72; 12 22; 19 32; 21 36]; 	
	%dx = [8 12 16 4 6 8 2 3 4];	% Minimum offset between rects in axis x for every layer
	%dy = [4 4 8 2 2 4 1 1 2];	% Minimum offset between rects in axis y for every layer
	%cut = [6 8 10 3 4 5 1 2 2];	% # of pixels to cut at the top and bottom (1/8 of height) after merge boxes 
	%% from one layer. This could be automatic in the future with no linear estimation
%else
	%% For 640x480 images
	%% boxdim = [112 184; 172 272; 56 92; 86 136; 28 46; 43 68]; % Actually it is one more pixel... 
	%boxdim = [76 128; 116 188; 38 64; 58 94; 28 46; 29 47]; % Actually it is one more pixel... 
	%dx = [20 32 10 16 5 8];	% Minimum offset between rects in axis x for every layer
	%dy = [8 16 4 8 2 4];	% Minimum offset between rects in axis y for every layer
	%cut = [14 21 7 11 3 5]; % # of pixels to cut at the top and bottom (1/8 of height) after merge boxes 
	%% from one layer. This could be automatic in the future with no linear estimation
%end

%%Try and "compute" the values for boxdim, dx, dy and cut (as shown above) automatically from the input boxes!!
boxdim = [unique(bottom-top,'rows'), unique(right-left,'rows')];
dx = boxdim(:,2)/8;
dy = boxdim(:,1)/8;
cut = dx-dy; 

%%%Sanity checks for automatic boxdim stuffs
disp('Box dim stuff')
disp(size(boxdim))
disp('dx')
disp(size(dx))
disp(size(dy))

% Initializing accumulators
times = [];		% To store times ***
ntrecs = [];	% To store total number of recs ***

%system("ls images/cestest????.png > list.txt");
%fname = textread("list.txt", "%s");
% fname{1} = "images/cestest6067.png";
%Nima = size(fname, 1);		% Number of images for testing ***
Nima = 1; %Setting the number of images to 1, because we are trying to make this a function!
Nlayers = size(boxdim, 1);	% Number of layers (9 or 6 for our text detector parameters so far)

% This cells contain partial results for every image (Nima in total). These hold variable size data
lines = cell(Nima, Nlayers);	% cell to store estimated initial and ending row of lines per layer and image
hists = cell(Nima, Nlayers);	% cell to store histograms of lines per layer and image
boxes = cell(Nima, 1);

% For every image in the test set
for indima = 1:Nima
	% Load recs info (layer, corners and weight). Data is sorted by layer, then top, then left values
%	if smallimage
		% filename = sprintf('temp/320x240/td%.2ds50', indima);
%		filename = fname{indima}(1:end-4);
%	else		
		% filename = sprintf('temp/640x480/td%.2d', indima);
%		filename = fname{indima}(1:end-4);
%	end
	%This value comes in from the python/rigor/TD/call()
%	[layer, top, left, bottom, right, weight] = textread(sprintf('%s_rects.txt', filename),...
%	'%d %d %d %d %d %f', 'headerlines', 1);
%  [layer, top, left, bottom, right] = rect_info; 
	%try 	load(sprintf('%s_heatmap', fn))
	%	disp(sprintf('%s_heatmap loaded', fn)), fflush(stdout);
	%catch

	% Group rects with similar top value for every layer. These groups may correspond to the same line of text 
	tic		% Start chronometer ***
	nrecs = length(layer);			% Number of rects loaded
	ini_layer = layer(1) + 1;		% Initial layer. "+1" to avoid starting from ZERO as index
	end_layer = layer(nrecs) + 1;	% Final layer. Also "+1"

	%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
	% Getting lines and its histograms for every layer
	for ind_layer = ini_layer:end_layer 
		id_layer = find(layer == ind_layer-1);	% Get identifiers (indexes) for current layer
		line_limits = []; 				% Acumulator for initial and final row and column per "line of text" ***
		line_hist_acc = [];				% Histogram's accumulator for every line ***
		nrec_layer = length(id_layer);	% Number of recs for current layer
		if nrec_layer > 0
			% Starting from first box for this layer
			ini_id = 1;							% Index for initial rec of current line
			ini_row = top(id_layer(ini_id));	% Initial and ending row for top of boxes set to the first one
			end_row = ini_row;
			for ind_rec = 2:nrec_layer			% For all other recs
				% Check if next box is "far" (next line). To test later: 2*dy ...  
				if (top(id_layer(ind_rec)) > end_row + dy(ind_layer))
					% New group found so we store previous group
					end_row = end_row + boxdim(ind_layer,1);	% Compute last row adding height of rec 
					% Columns estimation
					line_left = left(id_layer(ini_id):id_layer(ind_rec-1));		% Get all left values for this line
					line_right = right(id_layer(ini_id):id_layer(ind_rec-1)); 	% Get all right values for this line
					ini_col = min(line_left);				% Initial x coordinate for line
					end_col = max(line_right);				% Final x coordinate for line
					%line_left = line_left/dx(ind_layer);	
					% Normalizing for histograms (avoiding gaps)
					ini_left = ini_col/dx(ind_layer); 		% Same as min(line_left);
					end_left = max(line_left)/dx(ind_layer);

					% Compute histogram of left values
					linehist = hist(left(id_layer(ini_id):id_layer(ind_rec-1)), end_left - ini_left + 1);

					% For every box counted, "expand it" to the right --->
					linehist2 = conv(ones(1,round(boxdim(ind_layer,2)/dx(ind_layer))), linehist);

					% Storing coordinates 
					line_limits = [line_limits; ini_row+cut(ind_layer) end_row-cut(ind_layer) ini_col end_col];
					
					% Storing histograms and resize if it is required
					line_hist_acc = [line_hist_acc zeros(size(line_hist_acc,1), size(linehist2,2) - size(line_hist_acc,2)); linehist2  zeros(1, size(line_hist_acc,2) - size(linehist2,2))]; % ***

					% Limits for next group of boxes
					ini_row = top(id_layer(ind_rec));
					end_row = ini_row;
					ini_id = ind_rec;
				else
					end_row = top(id_layer(ind_rec));	% Update the new end_row (optimize: only when it changes!)
				end
			end
			end_row = end_row + boxdim(ind_layer,1);	% Add height of rec

			% Columns estimation for last line (same as above) with "nrec_layer" instead of "ind_rec-1"
			line_left = left(id_layer(ini_id):id_layer(nrec_layer));
			line_right = right(id_layer(ini_id):id_layer(nrec_layer));
			ini_col = min(line_left);
			end_col = max(line_right);
			ini_left = ini_col/dx(ind_layer);
			end_left = max(line_left)/dx(ind_layer);
			linehist = hist(left(id_layer(ini_id):id_layer(nrec_layer)), end_left - ini_left + 1);
			linehist2 = conv(ones(1,round(boxdim(ind_layer,2)/dx(ind_layer))), linehist);

			line_limits = [line_limits; ini_row+cut(ind_layer) end_row-cut(ind_layer) ini_col end_col];
			line_hist_acc = [line_hist_acc zeros(size(line_hist_acc,1), size(linehist2,2) - size(line_hist_acc,2)); linehist2  zeros(1, size(line_hist_acc,2) - size(linehist2,2))];

			lines{indima, ind_layer} = line_limits;		% ***
			hists{indima, ind_layer} = line_hist_acc;	% ***
		end
	end

	time1 = toc;				% ***
	ntrecs = [ntrecs nrecs];	% ***

%	try 
%		im = imread(sprintf('%s_input.png', filename));
%	catch
%		system(sprintf("cp %s.png %s_input.png", filename, filename));
%		im = imread(sprintf('%s_input.png', filename));
%	end
	if size(im, 3) == 1
		im(:,:,2) = im;
		im(:,:,3) = im(:,:,1);
	end
	% Saving images with all boxes for every layer
	if savingimages
		draweverybox % Function to save many images, one per layer ***
	end

	%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
	% Getting boxes per line based on its histograms
	
	tic	
	myboxes = [];		% Array for storing boxes
	for ind_layer = layer(1)+1:Nlayers
		nlines = size(lines{indima, ind_layer}, 1);
		if nlines>0
			if savingimages
				im2 = im;
			end
			xoffset = dx(ind_layer); 	% Offset in x axis
			for ind_lines = 1:nlines
				look4newbox = 0;	% We just started with one box
				y1 = lines{indima, ind_layer}(ind_lines, 1) + 1;	% Coordinates for first box
				y2 = lines{indima, ind_layer}(ind_lines, 2) + 1;
				x1 = lines{indima, ind_layer}(ind_lines, 3) + 1;
				ini_h = 1;
				for ind_h = 2:size(hists{indima, ind_layer}, 2)		% For every element of the histogram
					if hists{indima, ind_layer}(ind_lines, ind_h) == 0	% If we find a hole (==0)
						if look4newbox==0								% If we are not looking for new box
							x2 = lines{indima, ind_layer}(ind_lines, 3) + 1 + xoffset*(ind_h - 1);	% End of box
							if savingimages
								im2([y1 y2], x1:x2, 1) = 255;
								im2([y1 y2], x1:x2, 2:3) = 0;
								im2(y1:y2, [x1 x2], 1) = 255;
								im2(y1:y2, [x1 x2], 2:3) = 0;
							end
							% Metric for the current box ("density" of boxes)
							density = mean(hists{indima, ind_layer}(ind_lines, ini_h:(ind_h - 1))); % or max!?
							% Store box data
							myboxes = [myboxes; y1 y2 x1 x2 ind_layer density];	% ***
							look4newbox = 1;	% Time to look for a new box
						end
					else
						if look4newbox==1	% We start a new box
							x1 = lines{indima, ind_layer}(ind_lines, 3) + 1 + xoffset*(ind_h - 1);
							ini_h = ind_h;
							look4newbox = 0;
						end
					end
				end
				if look4newbox == 0	% Same as above (for boxes that goes until the right extreme)
					x2 = lines{indima, ind_layer}(ind_lines, 3) + 1 + xoffset*(size(hists{indima, ind_layer}, 2) - 1);
					if savingimages
						im2([y1 y2], x1:x2, 1) = 255;
						im2([y1 y2], x1:x2, 2:3) = 0;
						im2(y1:y2, [x1 x2], 1) = 255;
						im2(y1:y2, [x1 x2], 2:3) = 0;
					end
					density = mean(hists{indima, ind_layer}(ind_lines, ini_h:(ind_h - 1)));
					myboxes = [myboxes; y1 y2 x1 x2 ind_layer density]; % ***
				end
			end
			if savingimages
				imwrite(im2, sprintf('%s_layer%.2d_merged.png', filename, ind_layer - 1));
			end
		end
	end
%	boxes{indima} = myboxes;

	time2 = toc;		% ***

	%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
	% Joining boxes across all layers

	tic
	boxh = myboxes(:,2) - myboxes(:,1) + 1;		% Box heights
	boxw = myboxes(:,4) - myboxes(:,3) + 1;		% Box widths

	% Sort by density value in descendent order
	[densv, densi] = sort(myboxes(:,6), 'descend');	
	sets = []; seq = [];
	boxvalue = ones(size(densv));	% state of the box: 1 for good box (default), -1 for discarded box
	
	% Thresholds for overlaping in x, y and area.
	lowth = 0.25;
	highth = 0.6;
	areath = 0.8;

	for ind1 = 1:length(boxvalue)		% For every box (box1)
		if densv(ind1) > 2				% with more than 2 for density value
			if boxvalue(densi(ind1))>0	% If the box is not discarded
				for ind2 = ind1+1:length(boxvalue)	% Compare with other boxes (box2) with lower density
					seq = [seq; ind1 ind2];		% Just to visualize the sequence of analysis
					% Height of box that contains both boxes
					box2h = max(myboxes([densi(ind1) densi(ind2)], 2)) - min(myboxes([densi(ind1) densi(ind2)], 1)) + 1;
					% Vertical overlap in pixels 
					ovy =  boxh(densi(ind1)) + boxh(densi(ind2)) - box2h; % overlap in y
					if ovy > 0	
						ovy1 = ovy/boxh(densi(ind1));	% Overlap ratio for box1 in y
						ovy2 = ovy/boxh(densi(ind2));	% Overlap ratio for box2 in y
						% Width of box that contains both boxes
						box2w = max(myboxes([densi(ind1) densi(ind2)], 4)) - min(myboxes([densi(ind1) densi(ind2)], 3)) + 1;
						% Horizontal overlap in pixels 
						ovx = boxw(densi(ind1)) + boxw(densi(ind2)) - box2w; % overlap in x
						if ovx > 0
							ovx1 = ovx/boxw(densi(ind1));	% Overlap ratio for box1 in x
							ovx2 = ovx/boxw(densi(ind2)); 	% Overlap ratio for box2 in x
							if (ovy1*ovx1 < highth && ovy2*ovx2 > areath)	% medium area overlap for box1 and high overlap for box2
								boxvalue(densi(ind2)) = -1;				% discard (... box2 contained in box1)
							else
								% Big condition for comparing boxes
								if ovy1 > highth && ovy2 > lowth && (ovx1 > highth || (ovx1 > lowth && ovx2 > highth))
									% Box2 for analysis
									sets = [sets; ind1 ind2 ovy1 ovy2 ovx1 ovx2 myboxes(densi(ind1),6) myboxes(densi(ind2),6)];
									ratio_density = myboxes(densi(ind2),6)/myboxes(densi(ind1),6);	% Ratio of density
									% Condition for changing boxes data based on box1 and box2
									if ratio_density > 0.6 && myboxes(densi(ind2),6) > 5 && boxh(densi(ind2))/boxh(densi(ind1)) < 1.8
										myboxes(densi(ind2),1) = round(mean([myboxes(densi(ind1),1) myboxes(densi(ind2),1)]));
										myboxes(densi(ind2),2) = round(mean([myboxes(densi(ind1),2), myboxes(densi(ind2),2)]));
										myboxes(densi(ind2),3) = min(myboxes(densi(ind1),3), myboxes(densi(ind2),3));
										myboxes(densi(ind2),4) = max(myboxes(densi(ind1),4), myboxes(densi(ind2),4));
										boxvalue(densi(ind1)) = -1;
										boxvalue(densi(ind2)) = 1;
									else
										boxvalue(densi(ind2)) = -1;
									end
								end
							end
						end % ovx > 0
					end % ovy > 0
				end
			end
		else
			boxvalue(densi(ind1)) = -1;
		end
	end

	time3 = toc;						% ***
	times = [times; time1 time2 time3];		% ***

	boxes{indima} = myboxes;

	%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
	% Saving images with final results
if savingimages
	im2 = im;
	final_id = find(boxvalue~=1);
	for indb = 1:length(final_id)
		x1 = myboxes(final_id(indb), 3);
		x2 = myboxes(final_id(indb), 4);
		y1 = myboxes(final_id(indb), 1);
		y2 = myboxes(final_id(indb), 2);
		im2([y1 y2], x1:x2, 1:2) = 220;
		im2([y1 y2], x1:x2, 3) = 0;
		im2(y1:y2, [x1 x2], 1:2) = 220;
		im2(y1:y2, [x1 x2], 3) = 0;
	end
	final_id = find(boxvalue==1);
	for indb = 1:length(final_id)
		x1 = myboxes(final_id(indb), 3);
		x2 = myboxes(final_id(indb), 4);
		y1 = myboxes(final_id(indb), 1);
		y2 = myboxes(final_id(indb), 2);
		im2([y1 y2], x1:x2, 1) = 255;
		im2([y1 y2], x1:x2, 2:3) = 0;
		im2(y1:y2, [x1 x2], 1) = 255;
		im2(y1:y2, [x1 x2], 2:3) = 0;
	end

	imwrite(im2, sprintf('%s_merginglayers.png', filename));

	figure(1), imagesc(im2), grid, axis image,
	for indt = 1:size(myboxes,1)
		text(myboxes(densi(indt), 3), myboxes(densi(indt), 1)+8, sprintf('(%d, %d)', indt, round(densv(indt))), 'color', 'red', 'fontsize', 15)
	end
	print(sprintf("%s_boxinfo.png", filename), '-color');

	im2 = im;
	final_id = find(boxvalue==1);
	for indb = 1:length(final_id)
		x1 = myboxes(final_id(indb), 3);
		x2 = myboxes(final_id(indb), 4);
		y1 = myboxes(final_id(indb), 1);
		y2 = myboxes(final_id(indb), 2);
		im2([y1 y2], x1:x2, 1) = 255;
		im2([y1 y2], x1:x2, 2:3) = 0;
		im2(y1:y2, [x1 x2], 1) = 255;
		im2(y1:y2, [x1 x2], 2:3) = 0;
	end

	imwrite(im2, sprintf('%s_zfinal.png', filename));
	disp(sprintf("Image %s_zfinal.png saved", filename)); fflush(stdout);
	
end
end
