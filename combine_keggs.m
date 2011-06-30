function combine_keggs(base_dir)
mkdir(base_dir, 'AllCombined');
outpath = fullfile(base_dir, 'AllCombined');
files = dir(base_dir);
dirs = {};
for i = 1:length(files)
    if files(i).isdir
        dirs{length(dirs)+1} = files(i).name; %#ok<AGROW>
    end
end
image_files = cell(size(dirs));
for i = 1:length(image_files)
    %[base_dir '/' dirs{i} '/*.png']
    image_files{i} = arrayfun(@(x)(x.name), dir([base_dir '/' dirs{i} '/*.png']), 'uniformoutput', false);
end
uni_images = unique(cat(1,image_files{:}));
dirs(cellfun('isempty', image_files)) = [];
dirs
images = cell(size(uni_images));
for i = 1:length(images)
    display(['reading: ' uni_images{i}])
    imcell = cell(size(dirs));
    for k = 1:length(dirs)
        try
            imcell{k} = imread(fullfile(base_dir, dirs{k}, uni_images{i}));
        catch %#ok<*CTCH>
            1+1;
            
        end
    end
    pres_images = imcell(~cellfun('isempty', imcell));
    tmask = false(size(pres_images{1},1), size(pres_images{1},2));
    for k = 2:length(pres_images)
        tmask = tmask | sum(pres_images{1},3) ~= sum(pres_images{k},3);
    end
    nimg = pres_images{1};
    if any(tmask(:))
        con = bwconncomp(tmask);
        numimages = length(pres_images);
        L = labelmatrix(con);
        for k = 1:con.NumObjects
            wanted=true(numimages,1);
            for n = 1:numimages
                whitespots = all(pres_images{n}==255,3);
                wanted(n) = mean(reshape(whitespots(L==k), 1, []))==0;
            end
            wanted = find(wanted);
            top = find(any(L==k,2),1);
            bot = find(any(L==k,2),1, 'last');
            spaces = ceil(linspace(find(any(L==k,1),1), ...
                find(any(L==k,1),1, 'last'), ...
                length(wanted)+1));
            for n = 1:length(wanted)
                ninds = spaces(n):spaces(n+1);
                nimg(top:bot,ninds,:) = pres_images{wanted(n)}(top:bot,ninds,:);
                %imshow(nimg)
            end
        end
        %imshow(nimg)
        %drawnow
        %pause(1)
        imwrite(nimg,fullfile(outpath, [uni_images{i}]), 'png')
    end

end



