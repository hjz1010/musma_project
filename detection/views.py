from datetime import datetime, timedelta
from pytz     import timezone, utc

from django.http       import JsonResponse
from django.views      import View
from django.db.models  import Q

from .models import Detection, State

KST = timezone('Asia/Seoul')

class TestView(View):
    def get(self, request):
        ## 1페이지 장비별 당일 state 누적 시간
        # 일단 당일 필터링
        today_datetime  = datetime.datetime.now()
        today_date      = today_datetime.strftime('%Y-%m-%d')
        today_detection = Detection.objects.filter(datetime__gte=today_date)
        # 장비별 필터링.... 장비 구분이 안되는디ㅠㅠ
        truck      = today_detection.filter(detection_type__name='truck')
        excavators = today_detection.filter(detection_type__name='excavators')
        backhoe    = today_detection.filter(detection_type__name='backhoe')
        etc        = today_detection.filter(detection_type__name='etc')
        # state 별로 카운트 
        # truck_idle = truck.filter(state__name='idel').count()
        truck_state      = {state.state : truck.filter(state__state=state.state).count() for state in State.objects.all()}
        excavators_state = {state.state : excavators.filter(state__state=state.state).count() for state in State.objects.all()}
        backhoe_state    = {state.state : backhoe.filter(state__state=state.state).count() for state in State.objects.all()}
        
        # 반환할 데이터
        results = {'truck_state': truck_state, 'excavators_state': excavators_state, 'backhoe_state': backhoe_state}

        return JsonResponse({'message': 'SUCCESS', 'results': results},  status=200)

class EquipmentTotalView(View):
    def get(self, request):        
        ## 2페이지 중장비 통계
        # 운송장비: truck/ 작업장비: excavator, backhoe, , 로 분류
        # 각 장비별(시리얼 넘버별) 가동률 일/주/월 단위로 표출
        # 가동률 = (travel+load+unload)/(전체)
        
        # default > 일 단위
        # 셀렉트 박스 선택시 query parameter로 요청 
        # :8000?select=daily 
        # :8000?select=weekly 
        # :8000?select=monthly 
## 그냥 오늘 날짜기준? 아니면 날짜, 주, 월 선택???
## 정은님이랑 합의하기

        # 1. client에서 받은 request에서 query parameter 값을 추출
        # 2. detection 데이터에서 요청에 해당하는 기간만 filter
        # 2-1. Q함수로 query param에 따른 필터 조건 생성
        # 2-2. 위 조건을 넣어서 기간에 해당하는 detections filter
        # 3. 각 장비별로 state count 계산해서
        # 4. JsonResponse로 반환하기

        ## 1안. 오늘 기준으로 
        select  = request.GET.get('select')  

        ##############################################################
        # DateTimeField Detection.datetime received a naive datetime 
        # (2022-08-20 00:00:00) while time zone support is active.
        ##############################################################
        now            = datetime.datetime.utcnow()
        today_datetime = utc.localize(now).astimezone(KST)
        #today_date     = today_datetime.strftime('%Y-%m-%d') ## navie

        q = Q()

        if select == daily or not select:
            q &= Q(datetime__date=datetime.now())
            q &= Q(datetime__date=today_datetime)

        elif select == weekly:
            weekday = today_datetime.weekday() # 0:월, 1:화, 2:수, 3:목, 4:금, 5:토, 6:일
            mon_datetime = today_datetime - timedelta(days=weekday)
            q &= Q(datetime__gte=mon_datetime)
            
        elif select == monthly:
            month = today_datetime.month 
            q &= Q(datetime__month=month) 

        ## 2안. 날짜로 선택
        daily   = request.GET.get('daily')
        weekly  = request.GET.get('weekly')
        monthly = request.GET.get('monthly')

        q = Q()

        if daily:
            selected_date = datetime.strptime(daily,'%Y-%m-%d')
            selected_day = selected_date.day
            q &= Q(datetime__day=selected_day)  

        if weekly:
            selected_date = datetime.strptime(weekly,'%Y-%m-%d')
            start_date = selected_date - timedelta(days=selected_date.weekday())
            start_date = start_date.astimezone(KST)  # 안해도 결과는 나오지만 warning
            end_date = start_date + timedelta(days=7)
            q &= Q(datetime__range=[start_date, end_date])

        if monthly:
            selected_date = datetime.strptime(monthly,'%Y-%m-%d')
            selected_month = selected_date.month
            q &= Q(datetime__month=selected_month)      


        detection_by_period = Detection.objects.filter(q)  

        truck = detection_by_period.filter(detection_type__name = 'truck') 
                                                # 실제 데이터에서는 시리얼넘버 별로 해야할 듯
        excavators = detection_by_period.filter(detection_type__name = 'excavators')
        backhoe = detection_by_period.filter(detection_type__name = 'backhoe')

        truck_state      = {state.state : truck.filter(state__state=state.state).count() for state in State.objects.all()}
        excavators_state = {state.state : excavators.filter(state__state=state.state).count() for state in State.objects.all()}
        backhoe_state    = {state.state : backhoe.filter(state__state=state.state).count() for state in State.objects.all()}

        results = {'truck_state': truck_state, 'excavators_state': excavators_state, 'backhoe_state': backhoe_state}


        return JsonResponse({'message': 'SUCCESS', 'results': results},  status=200)
     
