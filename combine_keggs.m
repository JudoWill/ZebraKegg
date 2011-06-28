dirs = {'AllColoredPaths/All/',...
    'AllColoredPaths/Colon/',...
    'AllColoredPaths/Kidney/',...
    'AllColoredPaths/Liver/',...
    'AllColoredPaths/Lung/',...
    'AllColoredPaths/Pancreas/'}; 

image_files = cell(size(dirs));
for i = 1:length(image_files)
    image_files{i} = arrayfun(@(x)(x.name), dir([dirs{i} '*.png']), 'uniformoutput', false);
end
uni_images = unique(cat(1,image_files{:}));

images = cell(size(uni_images));
mask_cell = cell(size(uni_images));
for i = 1:length(images)
    display(['reading: ' uni_images{i}])
    imcell = cell(size(dirs));
    for k = 1:length(dirs)
        try
            imcell{k} = imread(fullfile(dirs{k}, uni_images{i}));
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
        imshow(nimg)
        drawnow
        pause(1)
        imwrite(nimg,fullfile('AllCombinedPaths', [uni_images{i}]), 'png')
    end

end



