T = [0: 0.25: 30]
Lp = 1000
Tp = 300

function [r] = z(t) 
    if(t <= 10) then
        r = 0.035*t
    elseif(t <= 15) then 
        r = 0.35;
    elseif(t <= 20) then 
        r = 0.06*t - 0.55;
    elseif(t <= 25) then
        r = 0.65;
    else
        r = -0.13*t + 3.9;
    end
endfunction

function [x] = f(T)
    for i=1:length(T)
        lumi = modulo((int)(rand()*100), 31) + 550; // [980 - 1020]
        temp = modulo((int)(rand()*100), 21) + 105; // [105 - 125]
        
        z_r = z(T(i))*(Tp+Lp)
        //disp(z_r)
        x(i) = z_r + (lumi + temp)
        
        x(i) = x(i)/((Tp+Lp) + (Tp+Lp))
        //x(i) = z(T(i))
    end
endfunction

y = f(T);
disp('size x: ', length(y))
disp('size T: ', length(T))
plot(T',y,'g')
