FasdUAS 1.101.10   ��   ��    k             l     ��  ��    "  Try to locate conda in path     � 	 	 8   T r y   t o   l o c a t e   c o n d a   i n   p a t h   
  
 l   � ����  Q    �     r    
    I   �� ��
�� .sysoexecTEXT���     TEXT  m       �     c o m m a n d   - v   c o n d a��    o      ���� 0 	condapath 	condaPath  R      ������
�� .ascrerr ****      � ****��  ��    k   �       l   ��  ��    8 2 Try known system-wide paths only (no $HOME paths)     �   d   T r y   k n o w n   s y s t e m - w i d e   p a t h s   o n l y   ( n o   $ H O M E   p a t h s )      r        J          !   m     " " � # # B / o p t / h o m e b r e w / a n a c o n d a 3 / b i n / c o n d a !  $ % $ m     & & � ' ' 0 / o p t / a n a c o n d a 3 / b i n / c o n d a %  ( ) ( m     * * � + + < / u s r / l o c a l / a n a c o n d a 3 / b i n / c o n d a )  ,�� , m     - - � . . > / u s r / l o c a l / m i n i c o n d a 3 / b i n / c o n d a��    o      ���� 0 possiblepaths possiblePaths   / 0 / r     1 2 1 m     3 3 � 4 4   2 o      ���� 0 	condapath 	condaPath 0  5 6 5 X    M 7�� 8 7 Q   / H 9 :�� 9 k   2 ? ; ;  < = < I  2 9�� >��
�� .sysoexecTEXT���     TEXT > b   2 5 ? @ ? o   2 3���� 0 p   @ m   3 4 A A � B B    - - v e r s i o n��   =  C D C r   : = E F E o   : ;���� 0 p   F o      ���� 0 	condapath 	condaPath D  G�� G  S   > ?��   : R      ������
�� .ascrerr ****      � ****��  ��  ��  �� 0 p   8 o   " #���� 0 possiblepaths possiblePaths 6  H I H l  N N��������  ��  ��   I  J K J l  N N�� L M��   L 2 , If conda not found, try system Python first    M � N N X   I f   c o n d a   n o t   f o u n d ,   t r y   s y s t e m   P y t h o n   f i r s t K  O�� O Z   N� P Q���� P =  N S R S R o   N O���� 0 	condapath 	condaPath S m   O R T T � U U   Q k   V� V V  W X W r   V ] Y Z Y m   V Y [ [ � \ \   Z o      ���� 0 
pythonpath 
pythonPath X  ] ^ ] r   ^ j _ ` _ J   ^ f a a  b c b m   ^ a d d � e e  p y t h o n 3 c  f�� f m   a d g g � h h  p y t h o n��   ` o      ����  0 pythoncommands pythonCommands ^  i j i l  k k��������  ��  ��   j  k l k X   k � m�� n m Q   } � o p q o k   � � r r  s t s r   � � u v u I  � ��� w��
�� .sysoexecTEXT���     TEXT w b   � � x y x m   � � z z � { {  c o m m a n d   - v   y o   � ����� 0 cmd  ��   v o      ���� 0 
pythonpath 
pythonPath t  | } | l  � ��� ~ ��   ~ 2 , Verify it's actually Python and get version     � � � X   V e r i f y   i t ' s   a c t u a l l y   P y t h o n   a n d   g e t   v e r s i o n }  � � � r   � � � � � I  � ��� ���
�� .sysoexecTEXT���     TEXT � b   � � � � � o   � ����� 0 
pythonpath 
pythonPath � m   � � � � � � �    - - v e r s i o n   2 > & 1��   � o      ���� 0 pythonversion pythonVersion �  ��� � Z   � � � ����� � E   � � � � � o   � ����� 0 pythonversion pythonVersion � m   � � � � � � �  P y t h o n �  S   � ���  ��  ��   p R      ������
�� .ascrerr ****      � ****��  ��   q r   � � � � � m   � � � � � � �   � o      ���� 0 
pythonpath 
pythonPath�� 0 cmd   n o   n q����  0 pythoncommands pythonCommands l  � � � l  � ���������  ��  ��   �  � � � l  � ��� � ���   � D > If no system Python found either, ask user to locate manually    � � � � |   I f   n o   s y s t e m   P y t h o n   f o u n d   e i t h e r ,   a s k   u s e r   t o   l o c a t e   m a n u a l l y �  � � � Z   �� � ��� � � =  � � � � � o   � ����� 0 
pythonpath 
pythonPath � m   � � � � � � �   � k   �� � �  � � � r   � � � � � n   � � � � � 1   � ���
�� 
bhit � l  � � ����� � I  � ��� � �
�� .sysodisAaleR        TEXT � m   � � � � � � � , P y t h o n / C o n d a   N o t   F o u n d � �� � �
�� 
mesS � m   � � � � � � � � N e i t h e r   C o n d a   n o r   P y t h o n   w a s   f o u n d   a u t o m a t i c a l l y .   W h a t   w o u l d   y o u   l i k e   t o   d o ? � �� � �
�� 
btns � J   � � � �  � � � m   � � � � � � �  L o c a t e   C o n d a �  � � � m   � � � � � � �  L o c a t e   P y t h o n �  ��� � m   � � � � � � �  C a n c e l��   � �� ���
�� 
dflt � m   � � � � � � �  L o c a t e   C o n d a��  ��  ��   � o      ���� 0 
userchoice 
userChoice �  � � � l  � ���������  ��  ��   �  ��� � Z   �� � � ��� � =  � � � � � o   � ����� 0 
userchoice 
userChoice � m   � � � � � � �  C a n c e l � L  ����   �  � � � =  � � � o  
���� 0 
userchoice 
userChoice � m  
 � � � � �  L o c a t e   C o n d a �  � � � Q  W � � � � k  7 � �  � � � r  # � � � I ���� �
�� .sysostdfalis    ��� null��   � �� ���
�� 
prmp � m   � � � � � � P l e a s e   l o c a t e   y o u r   c o n d a   e x e c u t a b l e   ( u s u a l l y   i n   a n a c o n d a 3 / b i n   o r   m i n i c o n d a 3 / b i n ) :��   � o      ���� 0 	condafile 	condaFile �  � � � r  $- � � � n  $+ � � � 1  '+��
�� 
psxp � o  $'���� 0 	condafile 	condaFile � o      ���� 0 	condapath 	condaPath �  � � � l ..�� � ���   �   Test if it works    � � � � "   T e s t   i f   i t   w o r k s �  ��� � I .7�� ���
�� .sysoexecTEXT���     TEXT � b  .3 � � � o  ./���� 0 	condapath 	condaPath � m  /2 � � � � �    - - v e r s i o n��  ��   � R      ������
�� .ascrerr ****      � ****��  ��   � k  ?W � �  � � � I ?T�� � �
�� .sysodisAaleR        TEXT � m  ?B � � � � �  I n v a l i d   C o n d a � �� � �
�� 
mesS � m  EH � � � � � d T h e   s e l e c t e d   f i l e   i s   n o t   a   v a l i d   c o n d a   e x e c u t a b l e . � �� ��
�� 
btns  J  KP �� m  KN �  O K��  ��   � �� L  UW����  ��   �  = Za	 o  Z]���� 0 
userchoice 
userChoice	 m  ]`

 �  L o c a t e   P y t h o n �� Q  d� k  g�  r  gv I gr����
�� .sysostdfalis    ��� null��   ����
�� 
prmp m  kn � � P l e a s e   l o c a t e   y o u r   P y t h o n   e x e c u t a b l e   ( u s u a l l y   c a l l e d   p y t h o n   o r   p y t h o n 3 ) :��   o      ���� 0 
pythonfile 
pythonFile  r  w� n  w~ 1  z~��
�� 
psxp o  wz���� 0 
pythonfile 
pythonFile o      ���� 0 
pythonpath 
pythonPath �� I ���� ��
�� .sysoexecTEXT���     TEXT  b  ��!"! o  ������ 0 
pythonpath 
pythonPath" m  ��## �$$    - - v e r s i o n��  ��   R      ������
�� .ascrerr ****      � ****��  ��   k  ��%% &'& I ����()
�� .sysodisAaleR        TEXT( m  ��** �++  I n v a l i d   P y t h o n) ��,-
�� 
mesS, m  ��.. �// f T h e   s e l e c t e d   f i l e   i s   n o t   a   v a l i d   P y t h o n   e x e c u t a b l e .- ��0��
�� 
btns0 J  ��11 2��2 m  ��33 �44  O K��  ��  ' 5�5 L  ���~�~  �  ��  ��  ��  ��   � k  ��66 787 l ���}9:�}  9 7 1 System Python found, ask if user wants to use it   : �;; b   S y s t e m   P y t h o n   f o u n d ,   a s k   i f   u s e r   w a n t s   t o   u s e   i t8 <=< r  ��>?> n  ��@A@ 1  ���|
�| 
bhitA l ��B�{�zB I ���yCD
�y .sysodisAaleR        TEXTC m  ��EE �FF  C o n d a   N o t   F o u n dD �xGH
�x 
mesSG b  ��IJI b  ��KLK b  ��MNM b  ��OPO m  ��QQ �RR b C o n d a   w a s   n o t   f o u n d ,   b u t   P y t h o n   i s   a v a i l a b l e   a t :  P o  ���w�w 0 
pythonpath 
pythonPathN o  ���v
�v 
ret L o  ���u
�u 
ret J m  ��SS �TT X W o u l d   y o u   l i k e   t o   u s e   s y s t e m   P y t h o n   i n s t e a d ?H �tUV
�t 
btnsU J  ��WW XYX m  ��ZZ �[[ " U s e   S y s t e m   P y t h o nY \�s\ m  ��]] �^^  C a n c e l�s  V �r_�q
�r 
dflt_ m  ��`` �aa " U s e   S y s t e m   P y t h o n�q  �{  �z  ? o      �p�p "0 usesystempython useSystemPython= b�ob Z  ��cd�n�mc = ��efe o  ���l�l "0 usesystempython useSystemPythonf m  ��gg �hh  C a n c e ld L  ���k�k  �n  �m  �o   � iji l ���j�i�h�j  �i  �h  j klk l ���gmn�g  m 9 3 If we have pythonPath but no condaPath, use Python   n �oo f   I f   w e   h a v e   p y t h o n P a t h   b u t   n o   c o n d a P a t h ,   u s e   P y t h o nl p�fp Z  ��qr�e�dq F  �sts = �uvu o  � �c�c 0 	condapath 	condaPathv m   ww �xx  t > yzy o  
�b�b 0 
pythonpath 
pythonPathz m  
{{ �||  r k  }}} ~~ r  ��� m  �� ���  p i p 3� o      �a�a 0 pipcmd pipCmd ��� Z  8���`�� E  $��� o   �_�_ 0 
pythonpath 
pythonPath� m   #�� ���  p y t h o n 3� r  '.��� m  '*�� ���  p i p 3� o      �^�^ 0 pipcmd pipCmd�`  � r  18��� m  14�� ���  p i p� o      �]�] 0 pipcmd pipCmd� ��� l 99�\�[�Z�\  �[  �Z  � ��� r  9P��� b  9L��� b  9H��� b  9D��� b  9@��� m  9<�� ��� N c d   ~ / D o c u m e n t s / G i t / l i n k e d i n - s c r a p e r   & &  � o  <?�Y�Y 0 pipcmd pipCmd� m  @C�� ��� @   i n s t a l l   - r   r e q u i r e m e n t s . t x t   & &  � o  DG�X�X 0 
pythonpath 
pythonPath� m  HK�� ���    g u i _ m a i n . p y� o      �W�W 0 runcmd runCmd� ��� l QQ�V�U�T�V  �U  �T  � ��� Q  Qz���� I T[�S��R
�S .sysoexecTEXT���     TEXT� o  TW�Q�Q 0 runcmd runCmd�R  � R      �P��O
�P .ascrerr ****      � ****� o      �N�N 0 errormsg errorMsg�O  � I cz�M��
�M .sysodisAaleR        TEXT� m  cf�� ��� 8 F a i l e d   t o   l a u n c h   a p p l i c a t i o n� �L��
�L 
mesS� b  in��� m  il�� ���  E r r o r :  � o  lm�K�K 0 errormsg errorMsg� �J��I
�J 
btns� J  qv�� ��H� m  qt�� ���  O K�H  �I  � ��G� L  {}�F�F  �G  �e  �d  �f  ��  ��  ��  ��  ��    ��� l     �E�D�C�E  �D  �C  � ��� l     �B���B  � 6 0 Continue with conda logic if conda was found...   � ��� `   C o n t i n u e   w i t h   c o n d a   l o g i c   i f   c o n d a   w a s   f o u n d . . .� ��� l     �A���A  � ( " Build bash initialization command   � ��� D   B u i l d   b a s h   i n i t i a l i z a t i o n   c o m m a n d� ��� l     �@���@  � E ? set bashInit to do shell script condaPath & " shell.bash hook"   � ��� ~   s e t   b a s h I n i t   t o   d o   s h e l l   s c r i p t   c o n d a P a t h   &   "   s h e l l . b a s h   h o o k "� ��� l ����?�>� r  ����� b  ����� b  ����� m  ���� ���  s o u r c e   $ (� o  ���=�= 0 	condapath 	condaPath� m  ���� ��� H   i n f o   - - b a s e ) / e t c / p r o f i l e . d / c o n d a . s h� o      �<�< 0 sourceconda sourceConda�?  �>  � ��� l     �;���;  � y s set listEnvsCmd to "bash -c " & quoted form of (bashInit & " && conda env list | awk '{print $1}' | grep -v '^#'")   � ��� �   s e t   l i s t E n v s C m d   t o   " b a s h   - c   "   &   q u o t e d   f o r m   o f   ( b a s h I n i t   &   "   & &   c o n d a   e n v   l i s t   |   a w k   ' { p r i n t   $ 1 } '   |   g r e p   - v   ' ^ # ' " )� ��� l ����:�9� r  ����� b  ����� o  ���8�8 0 sourceconda sourceConda� m  ���� ��� h   & &   c o n d a   e n v   l i s t   |   a w k   ' { p r i n t   $ 1 } '   |   g r e p   - v   ' ^ # '� o      �7�7 0 listenvscmd listEnvsCmd�:  �9  � ��� l     �6�5�4�6  �5  �4  � ��� l     �3���3  �   Get environments   � ��� "   G e t   e n v i r o n m e n t s� ��� l ����2�1� Q  ������ r  ����� n  ����� 2 ���0
�0 
cpar� l ����/�.� I ���- �,
�- .sysoexecTEXT���     TEXT  o  ���+�+ 0 listenvscmd listEnvsCmd�,  �/  �.  � o      �*�* 0 envlist envList� R      �)�(�'
�) .ascrerr ****      � ****�(  �'  � k  ��  I ���&
�& .sysodisAaleR        TEXT m  �� � B F a i l e d   t o   l i s t   C o n d a   e n v i r o n m e n t s �%	
�% 
mesS m  ��

 � H C o u l d   n o t   r e t r i e v e   e n v i r o n m e n t   l i s t .	 �$�#
�$ 
btns J  �� �" m  �� �  O K�"  �#   �! L  ��� �   �!  �2  �1  �  l     ����  �  �    l     ��   , & If config file exists, use cached env    � L   I f   c o n f i g   f i l e   e x i s t s ,   u s e   c a c h e d   e n v  l ���� r  �� b  �� n  �� !  1  ���
� 
psxp! l ��"��" I ���#$
� .earsffdralis        afdr# m  ���
� afdrasup$ �%�
� 
from% m  ���
� fldmfldu�  �  �   m  ��&& �'' $ L i n k e d I n V a l i d a t o r / o      ��  0 appsupportpath appSupportPath�  �   ()( l ��*��* r  ��+,+ b  ��-.- o  ����  0 appsupportpath appSupportPath. m  ��// �00  s e t t i n g s . c o n f i g, o      �� 0 
configfile 
configFile�  �  ) 121 l     ���
�  �  �
  2 343 l ��5�	�5 r  ��676 m  ���
� boovfals7 o      �� 0 usecache useCache�	  �  4 898 l �0:��: Q  �0;<=; k  #>> ?@? r  ABA I �C�
� .sysoexecTEXT���     TEXTC b  DED m  FF �GG  c a t  E n  HIH 1  �
� 
strqI o  � �  0 
configfile 
configFile�  B o      ���� 0 	cachedenv 	cachedEnv@ JKJ r  LML o  ���� 0 	cachedenv 	cachedEnvM o      ���� 0 envname envNameK N��N r  #OPO m  ��
�� boovtrueP o      ���� 0 usecache useCache��  < R      ������
�� .ascrerr ****      � ****��  ��  = r  +0QRQ m  +,��
�� boovfalsR o      ���� 0 usecache useCache�  �  9 STS l     ��������  ��  ��  T UVU l     ��WX��  W %  If no cached env, ask the user   X �YY >   I f   n o   c a c h e d   e n v ,   a s k   t h e   u s e rV Z[Z l 1�\����\ Z  1�]^����] H  15__ o  14���� 0 usecache useCache^ k  8�`` aba r  8Qcdc I 8M��ef
�� .gtqpchltns    @   @ ns  e o  8;���� 0 envlist envListf ��gh
�� 
prmpg m  >Aii �jj D S e l e c t   a   C o n d a   e n v i r o n m e n t   t o   u s e :h ��k��
�� 
inSLk J  DIll m��m m  DGnn �oo  b a s e��  ��  d o      ���� 0 	chosenenv 	chosenEnvb pqp Z  Rvrs����r = RWtut o  RU���� 0 	chosenenv 	chosenEnvu m  UV��
�� boovfalss k  Zrvv wxw I Zo��yz
�� .sysodisAaleR        TEXTy m  Z]{{ �|| 0 N o   e n v i r o n m e n t   s e l e c t e d .z ��}~
�� 
mesS} m  `c ��� ^ Y o u   m u s t   s e l e c t   a   c o n d a   e n v i r o n m e n t   t o   p r o c e e d .~ �����
�� 
btns� J  fk�� ���� m  fi�� ���  O K��  ��  x ���� L  pr����  ��  ��  ��  q ��� r  w���� n  w}��� 4  z}���
�� 
cobj� m  {|���� � o  wz���� 0 	chosenenv 	chosenEnv� o      ���� 0 envname envName� ��� l ����������  ��  ��  � ��� l ��������  �   Save choice   � ���    S a v e   c h o i c e� ��� I �������
�� .sysoexecTEXT���     TEXT� b  ����� m  ���� ���  m k d i r   - p  � n  ����� 1  ����
�� 
strq� o  ������  0 appsupportpath appSupportPath��  � ���� I �������
�� .sysoexecTEXT���     TEXT� b  ����� b  ����� b  ����� m  ���� ��� 
 e c h o  � n  ����� 1  ����
�� 
strq� o  ������ 0 envname envName� m  ���� ���    >  � n  ����� 1  ����
�� 
strq� o  ������ 0 
configfile 
configFile��  ��  ��  ��  ��  ��  [ ��� l     ��������  ��  ��  � ��� l     ������  � : 4 Build command to activate env and launch Python GUI   � ��� h   B u i l d   c o m m a n d   t o   a c t i v a t e   e n v   a n d   l a u n c h   P y t h o n   G U I� ��� l �������� r  ����� b  ����� b  ����� b  ����� o  ������ 0 sourceconda sourceConda� m  ���� ��� &   & &   c o n d a   a c t i v a t e  � n  ����� 1  ����
�� 
strq� o  ������ 0 envname envName� m  ���� ��� �   & &   c d   ~ / D o c u m e n t s / G i t / l i n k e d i n - s c r a p e r   & &   p i p   i n s t a l l   - r   r e q u i r e m e n t s . t x t   & &   p y t h o n   g u i _ m a i n . p y� o      ���� 0 fullcommand fullCommand��  ��  � ��� l �������� r  ����� b  ����� m  ���� ���  b a s h   - c  � n  ����� 1  ����
�� 
strq� o  ������ 0 fullcommand fullCommand� o      ���� 0 runcmd runCmd��  ��  � ��� l     ��������  ��  ��  � ��� l     ������  �   Run it   � ���    R u n   i t� ��� l     ������  � 
  try   � ���    t r y� ��� l     ������  �  	do shell script runCmd   � ��� . 	 d o   s h e l l   s c r i p t   r u n C m d� ��� l     ������  �   on error errorMsg   � ��� $   o n   e r r o r   e r r o r M s g� ��� l     ������  � _ Y	display alert "Failed to launch application" message "Error: " & errorMsg buttons {"OK"}   � ��� � 	 d i s p l a y   a l e r t   " F a i l e d   t o   l a u n c h   a p p l i c a t i o n "   m e s s a g e   " E r r o r :   "   &   e r r o r M s g   b u t t o n s   { " O K " }� ��� l     ������  �   end try   � ���    e n d   t r y� ��� l     ������  � : 4 Build command to activate env and launch Python GUI   � ��� h   B u i l d   c o m m a n d   t o   a c t i v a t e   e n v   a n d   l a u n c h   P y t h o n   G U I� ��� l �������� r  ����� m  ���� ��� @ ~ / D o c u m e n t s / G i t / l i n k e d i n - s c r a p e r� o      ���� 0 
projectdir 
projectDir��  ��  � ��� l �������� r  ��   b  �� o  ������ 0 
projectdir 
projectDir m  �� � 
 / . e n v o      ���� 0 envfile envFile��  ��  �  l     ��������  ��  ��   	 l     ��
��  
 , & Check if BRAVE_API_KEY is set in .env    � L   C h e c k   i f   B R A V E _ A P I _ K E Y   i s   s e t   i n   . e n v	  l ������ r  �� m  �� �   o      ���� 0 apikey apiKey��  ��    l ����� Q  � r  � I �����
�� .sysoexecTEXT���     TEXT b  � b  �   m  ��!! �"" . g r e p   ' ^ B R A V E _ A P I _ K E Y = '    o  ������ 0 envfile envFile m   ## �$$ $   |   c u t   - d   ' = '   - f 2 -��   o      ���� 0 apikey apiKey R      ������
�� .ascrerr ****      � ****��  ��   r  %&% m  '' �((  & o      ���� 0 apikey apiKey��  ��   )*) l     ��������  ��  ��  * +,+ l �-����- Z  �./����. = #010 o  ���� 0 apikey apiKey1 m  "22 �33  / k  &�44 565 r  &;787 n  &79:9 1  37��
�� 
ttxt: l &3;����; I &3��<=
�� .sysodlogaskr        TEXT< m  &)>> �?? 2 E n t e r   y o u r   B R A V E _ A P I _ K E Y := ��@��
�� 
dtxt@ m  ,/AA �BB  ��  ��  ��  8 o      ���� 0 userkey userKey6 C��C Z  <�DE��FD > <CGHG o  <?���� 0 userkey userKeyH m  ?BII �JJ  E Q  F�KLMK k  ItNN OPO l II��QR��  Q   Update or append the key   R �SS 2   U p d a t e   o r   a p p e n d   t h e   k e yP T��T I It��U��
�� .sysoexecTEXT���     TEXTU b  IpVWV b  IlXYX b  IhZ[Z b  Id\]\ b  I`^_^ b  I\`a` b  IXbcb b  ITded b  IPfgf m  ILhh �ii 4 g r e p   - q   ' ^ B R A V E _ A P I _ K E Y = '  g o  LO�� 0 envfile envFilee m  PSjj �kk b   & &   s e d   - i   ' '   ' s / ^ B R A V E _ A P I _ K E Y = . * / B R A V E _ A P I _ K E Y =c o  TW�~�~ 0 userkey userKeya m  X[ll �mm  / '  _ o  \_�}�} 0 envfile envFile] m  `cnn �oo 0   | |   e c h o   ' B R A V E _ A P I _ K E Y =[ o  dg�|�| 0 userkey userKeyY m  hkpp �qq 
 '   > >  W o  lo�{�{ 0 envfile envFile��  ��  L R      �zr�y
�z .ascrerr ****      � ****r o      �x�x 0 errmsg errMsg�y  M k  |�ss tut I |��wvw
�w .sysodisAaleR        TEXTv m  |xx �yy : F a i l e d   t o   w r i t e   B R A V E _ A P I _ K E Yw �vz{
�v 
mesSz o  ���u�u 0 errmsg errMsg{ �t|�s
�t 
btns| J  ��}} ~�r~ m  �� ���  O K�r  �s  u ��q� L  ���p�p  �q  ��  F k  ���� ��� I ���o��
�o .sysodisAaleR        TEXT� m  ���� ���   A P I   k e y   r e q u i r e d� �n��
�n 
mesS� m  ���� ��� V Y o u   m u s t   e n t e r   a   B R A V E _ A P I _ K E Y   t o   c o n t i n u e .� �m��l
�m 
btns� J  ���� ��k� m  ���� ���  O K�k  �l  � ��j� L  ���i�i  �j  ��  ��  ��  ��  ��  , ��� l     �h�g�f�h  �g  �f  � ��� l     �e���e  �    Now launch the Python GUI   � ��� 4   N o w   l a u n c h   t h e   P y t h o n   G U I� ��� l ����d�c� r  ����� b  ����� b  ����� b  ����� b  ����� b  ����� o  ���b�b 0 sourceconda sourceConda� m  ���� ��� &   & &   c o n d a   a c t i v a t e  � n  ����� 1  ���a
�a 
strq� o  ���`�` 0 envname envName� m  ���� ���    & &   c d  � o  ���_�_ 0 
projectdir 
projectDir� m  ���� ��� r   & &   p i p   i n s t a l l   - r   r e q u i r e m e n t s . t x t   & &   p y t h o n   g u i _ m a i n . p y� o      �^�^ 0 fullcommand fullCommand�d  �c  � ��� l ����]�\� r  ����� b  ����� m  ���� ���  b a s h   - c  � n  ����� 1  ���[
�[ 
strq� o  ���Z�Z 0 fullcommand fullCommand� o      �Y�Y 0 runcmd runCmd�]  �\  � ��� l     �X�W�V�X  �W  �V  � ��U� l ���T�S� Q  ����� I ���R��Q
�R .sysoexecTEXT���     TEXT� o  ���P�P 0 runcmd runCmd�Q  � R      �O��N
�O .ascrerr ****      � ****� o      �M�M 0 errormsg errorMsg�N  � I ��L��
�L .sysodisAaleR        TEXT� m  ���� ��� 8 F a i l e d   t o   l a u n c h   a p p l i c a t i o n� �K��
�K 
mesS� b  ����� m  ���� ���  E r r o r :  � o  ���J�J 0 errormsg errorMsg� �I��H
�I 
btns� J  �� ��G� m  �� ���  O K�G  �H  �T  �S  �U       �F���F  � �E
�E .aevtoappnull  �   � ****� �D��C�B���A
�D .aevtoappnull  �   � ****� k    ��  
�� ��� ��� ��� �� (�� 3�� 8�� Z�� ��� ��� ��� ��� �� �� +�� ��� ��� ��@�@  �C  �B  � �?�>�=�<�? 0 p  �> 0 cmd  �= 0 errormsg errorMsg�< 0 errmsg errMsg� � �;�:�9�8 " & * -�7�6 3�5�4�3 A T [�2 d g�1 z ��0 � � � ��/ ��. � � ��- ��,�+�*�) � ��( ��'�&�% � � �
�$#*.3EQ�#SZ]`�"gw{�!�� ������������������
����&�/��F���i�n��{�����������
�	!#'2>�A���Ihjlnp�x����������
�; .sysoexecTEXT���     TEXT�: 0 	condapath 	condaPath�9  �8  �7 �6 0 possiblepaths possiblePaths
�5 
kocl
�4 
cobj
�3 .corecnte****       ****�2 0 
pythonpath 
pythonPath�1  0 pythoncommands pythonCommands�0 0 pythonversion pythonVersion
�/ 
mesS
�. 
btns
�- 
dflt�, 
�+ .sysodisAaleR        TEXT
�* 
bhit�) 0 
userchoice 
userChoice
�( 
prmp
�' .sysostdfalis    ��� null�& 0 	condafile 	condaFile
�% 
psxp�$ 0 
pythonfile 
pythonFile
�# 
ret �" "0 usesystempython useSystemPython
�! 
bool�  0 pipcmd pipCmd� 0 runcmd runCmd� 0 errormsg errorMsg� 0 sourceconda sourceConda� 0 listenvscmd listEnvsCmd
� 
cpar� 0 envlist envList
� afdrasup
� 
from
� fldmfldu
� .earsffdralis        afdr�  0 appsupportpath appSupportPath� 0 
configfile 
configFile� 0 usecache useCache
� 
strq� 0 	cachedenv 	cachedEnv� 0 envname envName
� 
inSL
� .gtqpchltns    @   @ ns  � 0 	chosenenv 	chosenEnv� 0 fullcommand fullCommand� 0 
projectdir 
projectDir�
 0 envfile envFile�	 0 apikey apiKey
� 
dtxt
� .sysodlogaskr        TEXT
� 
ttxt� 0 userkey userKey� 0 errmsg errMsg�A �j E�WzX  �����vE�O�E�O -�[��l kh   ��%j O�E�OW X  h[OY��O�a  0a E` Oa a lvE` O U_ [��l kh  2a �%j E` O_ a %j E` O_ a  Y hW X  a E` [OY��O_ a   �a a a a a  a !a "mva #a $a % &a ',E` (O_ (a )  hY �_ (a *  K (*a +a ,l -E` .O_ .a /,E�O�a 0%j W X  a 1a a 2a a 3kv� &OhY Z_ (a 4  O ,*a +a 5l -E` 6O_ 6a /,E` O_ a 7%j W X  a 8a a 9a a :kv� &OhY hY Ka ;a a <_ %_ =%_ =%a >%a a ?a @lva #a Aa % &a ',E` BO_ Ba C  hY hO�a D 	 _ a Ea F& ma GE` HO_ a I a JE` HY 	a KE` HOa L_ H%a M%_ %a N%E` OO _ Oj W X P a Qa a R�%a a Skv� &OhY hY hOa T�%a U%E` VO_ Va W%E` XO _ Xj a Y-E` ZW X  a [a a \a a ]kv� &OhOa ^a _a `l aa /,a b%E` cO_ ca d%E` eOfE` fO &a g_ ea h,%j E` iO_ iE` jOeE` fW X  fE` fO_ f z_ Za +a ka la mkv� nE` oO_ of  a pa a qa a rkv� &OhY hO_ o�k/E` jOa s_ ca h,%j Oa t_ ja h,%a u%_ ea h,%j Y hO_ Va v%_ ja h,%a w%E` xOa y_ xa h,%E` OOa zE` {O_ {a |%E` }Oa ~E` O a �_ }%a �%j E` W X  a �E` O_ a �  �a �a �a �l �a �,E` �O_ �a � Q 0a �_ }%a �%_ �%a �%_ }%a �%_ �%a �%_ }%j W X � a �a �a a �kv� &OhY a �a a �a a �kv� &OhY hO_ Va �%_ ja h,%a �%_ {%a �%E` xOa �_ xa h,%E` OO _ Oj W X P a �a a ��%a a �kv� & ascr  ��ޭ